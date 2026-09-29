/*
 ==============================================================================
 
 ScalaUserModel.h
 Created: 15 Oct 2022 2:19:29pm
 Author:  Marcus W. Hobbs
 
 ==============================================================================
 */

#pragma once

#include <JuceHeader.h>
#include "Columns.h"
#include "FavoritesIconRenderer.h"
#include "ScalaIconRenderer.h"
#include "ScalaModelProtocol.h"
#include "ScalaTuningImp.h"
#include "Tuning_Include.h"

class ScalaUserModel final
: public ScalaModelProtocol
, private ActionBroadcaster
{
public:
    // lifecycle
    ScalaUserModel(File xmlFile, File scalafileDirectory, File iconCacheDirectory);
    ~ScalaUserModel() noexcept override = default;
private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(ScalaUserModel)
    
public:
    // public methods
    // given .scl and optional .kbm: creates ID, Icon, Period, NPO, Description
    // and adds to database...does not modify filesystem!
    // Works for "user" only, because only it is writeable
    bool addScalaKbm(File scl_file, File kbm_file);
    bool addScalaFromTuning(shared_ptr<Tuning> tuning, bool create_kbm);
    shared_ptr<ScalaTuningImp> getScalaTuningForID(int ID) override; // return nullptr if ID is out of range
    shared_ptr<ScalaTuningImp> getScalaTuningForRow(int row_number) override;// nullptr is ID is out of range
    int getIDForRow(int row_number);
    shared_ptr<ScalaTuningImp> recallPreviousScala() override;
    shared_ptr<ScalaTuningImp> recallNextScala() override;
    bool deleteScalaTuningAtRow(int row_number);
    int getSelectedRowNumber() override;
    int getSelectedID() override;
    unordered_map<int, int> getIntegrityCheck() override;

    // TableListBoxModel delegates
    int getNumRows() override;
    int getColumnAutoSizeWidth(int column_id) override;
    void sortOrderChanged(int new_sort_column_id, bool is_forwards) override;
    Font getFont();
    String getText(int row_number, int column_id) override;
    void setText(String column_name, const int row_number, const String& new_text);
    int getIsSelectedForRow(const int row_number) const override;
    void selectRow(const int row_number) override;
    vector<Columns> getColumns();
    shared_ptr<Image> getIcon(int row_number) override;
    
private:
    // private members
    File _xmlFile;
    File _scalaFileDirectory;
    File _iconCacheDirectory;
    vector<Columns> _columns; // init at construction and never mutated
    unique_ptr<XmlElement> _scalaLibrary; // OWNER
    XmlElement* _columnList = nullptr;
    XmlElement* _dataList = nullptr;
    int _selectedID = -1;
    Font _font {FontOptions{WilsonicAppSkin::tableViewFontSize}};
    CriticalSection _lock;
    
    // private methods
    File _fullPathToSclFile(String file_name); // helper, you need to validate
    File _fullPathToIconFile(String file_name); // for icon
    String _getIconFilename(int row_number);
    bool _writeScalaLibraryToDisk();
    void _logXML();
    String _getAttributeNameForColumnId(const int column_id) const;
    int _getNewID();
    int _getRowForID(int id_number);
    
    // private helper class
    class ScalaLibraryDataSorter
    {
    public:
        ScalaLibraryDataSorter(const String& attribute_to_sort_by, bool forwards)
        :_attributeToSort(attribute_to_sort_by)
        ,_direction(forwards ? 1 : -1)
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
