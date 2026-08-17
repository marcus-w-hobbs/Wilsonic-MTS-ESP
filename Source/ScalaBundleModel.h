/*
 ==============================================================================
 
 ScalaBundleModel.h
 Created: 3 Apr 2023 8:36:36pm
 Author:  Marcus W. Hobbs
 
 ==============================================================================
 */

#pragma once

class ScalaBundleModel;

#include <JuceHeader.h>
#include "Columns.h"
#include "FavoritesIconRenderer.h"
#include "ScalaIconRenderer.h"
#include "ScalaModelProtocol.h"
#include "ScalaTuningImp.h"
#include "Tuning_Include.h"

// this class reads a "bundled" BinaryData xml file.

class ScalaBundleModel final 
: public ScalaModelProtocol
{
public:
    // lifecycle
    ScalaBundleModel(File iconCacheDirectory);
    ~ScalaBundleModel() noexcept override = default;
private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(ScalaBundleModel)
    
public:
    // public methods
    shared_ptr<ScalaTuningImp> getScalaTuningForID(int ID) override; // return nullptr if row is out of range
    shared_ptr<ScalaTuningImp> getScalaTuningForRow(int row_number) override;
    shared_ptr<ScalaTuningImp> recallPreviousScala() override;
    shared_ptr<ScalaTuningImp> recallNextScala() override;
    int getSelectedRowNumber() override;
    int getSelectedID() override;
    unordered_map<int, int> getIntegrityCheck() override;

    // TableListBoxModel delegates
    int getNumRows() override;
    int getColumnAutoSizeWidth(int column_id) override;
    void sortOrderChanged(int new_sort_column_id, bool is_forwards) override;
    String getText(int row_number, int column_id) override;
    int getIsSelectedForRow(const int row_number) const override;
    void selectRow(const int row_number) override;
    shared_ptr<Image> getIcon(int row_number) override;
    
private:
    // private members
    File _iconCacheDirectory;
    vector<Columns> _columns; // init at construction and never mutated
    unique_ptr<XmlElement> _scalaLibrary; // OWNER
    XmlElement* _columnList = nullptr;
    XmlElement* _dataList = nullptr;
    int _selectedID = -1;
    Font _font {FontOptions{WilsonicAppSkin::tableViewFontSize}};
    CriticalSection _lock;
    
    // private methods
    File _fullPathToIconFile(String file_name); // for icon
    String _getIconFilename(int row_number);
    void _logXML();
    String _getAttributeNameForColumnId(const int column_id) const;
    int _getIDForRow(int row_number);
    int _getRowForID(int id_number);
    
    // private helper class
    class ScalaLibraryDataSorter
    {
    public:
        ScalaLibraryDataSorter(const String& attribute_to_sort_by, bool forwards)
        : _attributeToSort(attribute_to_sort_by)
        , _direction(forwards ? 1 : -1)
        {}
        
        int compareElements(XmlElement* first, XmlElement* second) const
        {
            auto result = first->getStringAttribute(_attributeToSort)
                .compareNatural(second->getStringAttribute(_attributeToSort));
            if(result == 0)
            {
                result = first->getStringAttribute("ID")
                    .compareNatural(second->getStringAttribute("ID"));
            }
            
            return _direction * result;
        }
        
    private:
        String _attributeToSort;
        int _direction;
    };
};
