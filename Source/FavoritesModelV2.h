/**
 * @file FavoritesModelV2.h
 * @brief This file contains the FavoritesModelV2 class.
 * @author Marcus W. Hobbs
 * @date Created: 9 Jul 2022 7:19:13pm
 */

#pragma once

#include <JuceHeader.h>
#include "Columns.h"
#include "Favorite.h"
#include "ModelBase.h"
#include "Tuning_Include.h"
#include "Tuning.h"

// forward
class WilsonicProcessor;
class MorphModel;
class MorphABModel;
class MorphFavoritesAComponent;
class MorphFavoritesBComponent;

/**
 * @class FavoritesModelV2
 * @brief This class is responsible for managing the favorites model.
 */
class FavoritesModelV2 final
: public ModelBase
, public ActionBroadcaster
, public ActionListener
{
public:
    // static members
    static const String getFavoritesModelV2UpdateUIMessage() { return "getFavoritesModelV2UpdateUIMessage"; }
    static const ParameterID getFavoritesIDParameterID() { return ParameterID("FAVORITESID", AppVersion::getVersionHint()); }
    static const String getFavoritesIDParameterName() { return "Wilsonic|Favorites ID"; }

    // if you change these you will break Favorites, and Morph automation
    static constexpr int getFavoritesMinID() {return 0;}
    static constexpr int getFavoritesMaxID() {return 8191;}

    //
    enum class DataList {
        Favorites = 0,
        FavoritesA = 1,
        FavoritesB = 2
    };

    // lifecycle
    FavoritesModelV2(WilsonicProcessor& processor);
    ~FavoritesModelV2() override;
private:
    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(FavoritesModelV2)

public:
    // public methods

    // ModelBase
    shared_ptr<Tuning> getTuning() override;
    unique_ptr<AudioProcessorParameterGroup> createParams() override;
    String getGroupID() override;
    String getGroupName() override;
    String getSubgroupSeparator() override;
    ParameterID getDesignParameterID() override; // key for this design's Favorites array
    StringArray getFavoritesParameterIDs() override; // used for Favorites
    void attachParameterListeners() override;// called only once: when assigning _avpts
    void detachParameterListeners() override;
    void parameterChanged(const String& parameterID, float newValue) override;
    void updateProperties() override;
    void _tuningChangedUpdateUI() override;

    /**
     * @brief Add a favorite.
     * @param design_index The design index.
     * @param design_description The design description.
     * @param npo The npo.
     * @param tuning_description The tuning description.
     * @param tuning_param_description The tuning parameter description.
     * @param param_keys The parameter keys.
     * @param tuning The tuning.
     */
    void uiAddNewFavorite(unsigned long design_index,
                          String design_description, /* passed in based on _designsNames */
                          unsigned long npo,
                          String tuning_description,
                          String tuning_param_description,
                          StringArray param_keys,
                          shared_ptr<Tuning> tuning);
    void uiStoreCurrentTuningAsFavorite();
    void uiRecallFavoriteAtRowNumber(int row_number);
    void uiDeleteFavoriteAtRowNumber(int row_number);
    float uiGetFavoriteID();
    void uiSetFavoriteID(float ID, String status_message = "");
    void uiRecallPreviousFavorite();
    void uiRecallNextFavorite();

    // ActionListener
    void actionListenerCallback(const String&) override;
    
    // TableListBoxModel delegates
    vector<Columns> getColumns();
    int getNumRows(DataList dataList);
    int getFavoriteRowNumber(DataList dataList);
    int getColumnAutoSizeWidth(int columnId);
    void sortOrderChanged(int newSortColumnId, bool isForwards, DataList dataList);
    Font getFont();
    String getText(int rowNumber, int columnId, DataList dataList);
    void setText(String columnName, const int rowNumber, const String& newText); // not for A,B
    int getSelection(const int rowNumber, DataList dataList) const;
    void setSelection(const int rowNumber, const int newSelection, DataList dataList);
    shared_ptr<Image> getIcon(int rowNumber, DataList dataList);

private:
    // private members
    WilsonicProcessor& _processor;
    vector<Columns> _columns; // init at construction and never mutated
    unique_ptr<XmlElement> _favoritesLibrary; // OWNER
    XmlElement* _columnList = nullptr;
    XmlElement* _dataList = nullptr; // unfiltered
    unique_ptr<XmlElement> _dataListA = nullptr; // filtered out Morph
    unique_ptr<XmlElement> _dataListB = nullptr; // filtered out Morph
    Font _font {FontOptions{14.0f}};
    int _favoriteRowNumber = 0; // source of truth for favoritesA,B are based on ID's from MorphModel
    int _favoriteID = -1; // set by model, throttled by updateUI
    int _favoriteIDHost = -1; // set by host in parameterChanged
    String _status_message = "";

    // private methods
    void _uiRecallFavoriteInternal(int favorite_row_number); // this actually recalls the favorite
    bool _deleteFavoriteID(int favoriteID); // returns success
    bool _performUserScalaIntegrityCheck();
    bool _performFavoritesIntegrityCheck();
    bool _writeFavoritesToDisk();
    File _getFavoritesLibraryFile();
    void _logXML();
    String _getAttributeNameForColumnId(const int columnId) const;
    int _getNewID();
    unique_ptr<XmlElement> _getDataListNonMorph();
    unordered_map<int, int> _getNonMorphIntegrityCheck();

    // friend helpers
    Favorite _getFavoriteForID(int ID);
    int _IDForRowNumber(int rowNumber, DataList dataList);
    int _rowNumberForID(int ID, DataList dataList);
    friend class MorphModel;
    friend class MorphABModel;
    friend class MorphFavoritesAComponent;
    friend class MorphFavoritesBComponent;
    
    // private helper class
    class FavoritesDataSorter {
    public:
        FavoritesDataSorter(const String& attributeToSortBy, bool forwards)
        : _attributeToSort(attributeToSortBy)
        , _direction(forwards ? 1 : -1)
        {}
        int compareElements(XmlElement* first, XmlElement* second) const {
            auto result = first->getStringAttribute(_attributeToSort)
                .compareNatural(second->getStringAttribute(_attributeToSort));
            if(result == 0) {
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
