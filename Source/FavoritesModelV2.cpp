/*
 ==============================================================================
 
 FavoritesModelV2.cpp
 Created: 9 Jul 2022 7:19:13pm
 Author:  Marcus W. Hobbs
 
 ==============================================================================
 */

#include "DesignsModel.h"
#include "FavoritesComponentMessageBus.h"
#include "FavoritesModelV2.h"
#include "FavoritesIconRenderer.h"
#include "MorphModel.h"
#include "ScalaModel.h"
#include "WilsonicProcessor.h"

#pragma mark - Lifecycle

FavoritesModelV2::FavoritesModelV2(WilsonicProcessor& processor)
: _processor(processor)
{
    auto favorites_library = _getFavoritesLibraryFile();
    auto favorites_fullpath = favorites_library.getFullPathName();
    
    //  true: debug(fresh start)
    // false: prod(bau)
#if false
    // use this code path to simulate a fresh install
    
    // delete library file
    auto delete_success = favorites_library.deleteFile();
    if(delete_success) {
        // debug: remove local library
        // success = successfully deleted, or there was not a file to delete
        DBG("DEBUG: Fresh start: " << favorites_fullpath);
    } else {
        DBG("DEBUG: Error deleting previous file:" << favorites_fullpath);
        DBG("DEBUG: Reading existing file on disk: " << favorites_fullpath);
    }
    
    // delete icons
    FavoritesIconRenderer::debugDeleteAllIcons();
#else
    //DBG("DEBUG: Reading existing file on disk: " << favorites_fullpath);
#endif
    
    // null or empty file...Create and Save
    if(favorites_library == File() || ! favorites_library.exists()) {
        // <FAVORITES_DATA>
        XmlElement favorites_data("FAVORITES_DATA");
        
        //   <COLUMNS>
        XmlElement* columns = new XmlElement("COLUMNS");
        favorites_data.addChildElement(columns);
        auto add_column = [&](int columnId, String name, int width, int visible, int editable, int sortable) {
            XmlElement* column = new XmlElement("COLUMN");
            column->setAttribute("columnId", columnId);
            column->setAttribute("name", name);
            column->setAttribute("width", width);
            column->setAttribute("visible", visible);
            column->setAttribute("editable", editable);
            column->setAttribute("sortable", sortable);
            columns->addChildElement(column);
        };
        
        // if you change any of these properties you must recreate xml
        auto const iw = FavoritesIconRenderer::icon_dimension;
        add_column(1, "ID"            ,  25, 1, 0, 1);
        add_column(2, "Icon"          ,  iw, 1, 0, 0);
        add_column(3, "Design"        , 160, 1, 0, 1);
        add_column(4, "NPO"           ,  30, 1, 0, 1);
        add_column(5, "Description"   , 250, 1, 1, 1);
        add_column(6, "Parameters"    , 450, 1, 0, 1);
        add_column(7, "Parameter_Hash", 250, 0, 0, 0);
        // add_column(8, "MIDI_Learn", 150);
        
        //   </DATA>
        XmlElement* data = new XmlElement("DATA");
        favorites_data.addChildElement(data);
        
        // </FAVORITES_DATA>
        
        // assign and save
        _favoritesLibrary = make_unique<XmlElement>(std::move(favorites_data));
        jassert(_favoritesLibrary != nullptr);
        // must be a valid favorites library
        jassert(_favoritesLibrary != nullptr);
        _dataList = _favoritesLibrary->getChildByName("DATA");
        jassert(_dataList != nullptr);
        _dataListA = _getDataListNonMorph();
        _dataListB = _getDataListNonMorph();
        _columnList = _favoritesLibrary->getChildByName("COLUMNS");
        jassert(_columnList != nullptr);
        _writeFavoritesToDisk();
    } else {
        // just read and validate
        _favoritesLibrary = XmlDocument::parse(favorites_library);
        // must be a valid favorites library
        jassert(_favoritesLibrary != nullptr);
        _dataList = _favoritesLibrary->getChildByName("DATA");
        jassert(_dataList != nullptr);
        _dataListA = _getDataListNonMorph();
        _dataListB = _getDataListNonMorph();
        _columnList = _favoritesLibrary->getChildByName("COLUMNS");
        jassert(_columnList != nullptr);
    }
    
    // visible columns have these flags:
    auto const visibleFlag =
    TableHeaderComponent::visible |
    TableHeaderComponent::resizable |
    TableHeaderComponent::draggable |
    TableHeaderComponent::resizable |
    TableHeaderComponent::appearsOnColumnMenu |
    TableHeaderComponent::sortable;
    for(auto* columnXml : _columnList->getChildIterator()) {
        Columns c(columnXml->getStringAttribute("name"),
                  columnXml->getIntAttribute("columnId"),
                  columnXml->getIntAttribute("width"),
                  50, // unused actually
                  400, // unused actually
                  visibleFlag, // overwritten later if visible == 0
                  -1, // insertIndex, unused
                  columnXml->getIntAttribute("visible"),
                  columnXml->getIntAttribute("editable"),
                  columnXml->getIntAttribute("sortable")
                  );
        _columns.push_back(c);
    }
    
    // _columns is never mutated after this
    
    // debug
    //_logFavoritesXML();
}

FavoritesModelV2::~FavoritesModelV2() {
    
}

#pragma mark - ModelBase

shared_ptr<Tuning> FavoritesModelV2::getTuning() {
    jassertfalse;
    return nullptr;
}

unique_ptr<AudioProcessorParameterGroup> FavoritesModelV2::createParams() {
    auto scaleGroup = make_unique<AudioProcessorParameterGroup>
    (getGroupID(), getGroupName(), getSubgroupSeparator(),
     make_unique<AudioParameterInt>
     (FavoritesModelV2::getFavoritesIDParameterID(),
      FavoritesModelV2::getFavoritesIDParameterName(),
      FavoritesModelV2::getFavoritesMinID(),
      FavoritesModelV2::getFavoritesMaxID(),
      FavoritesModelV2::getFavoritesMinID())
     );
    
    return scaleGroup;
}

String FavoritesModelV2::getGroupID() {
    return "Favorites";
}

String FavoritesModelV2::getGroupName() {
    // Return the group name
    return "Wilsonic";
}

String FavoritesModelV2::getSubgroupSeparator() {
    // Return the subgroup separator
    return " | ";
}

// doesn't make sense for Favorites
ParameterID FavoritesModelV2::getDesignParameterID() {
    // Return the design parameter ID
    return ParameterID("FAVORITES_PARAMETERID", AppVersion::getVersionHint());
}

StringArray FavoritesModelV2::getFavoritesParameterIDs() {
    return StringArray(getFavoritesIDParameterID().getParamID());
}

// called only once: after assigning _avpts
void FavoritesModelV2::attachParameterListeners() {
    jassert (_apvts != nullptr);
    for (auto pid : getFavoritesParameterIDs())  {
        _apvts->addParameterListener (pid, this);
    }
}

void FavoritesModelV2::detachParameterListeners() {
    jassert (_apvts != nullptr);
    for (auto pid : getFavoritesParameterIDs())  {
        _apvts->removeParameterListener (pid, this);
    }
}

void FavoritesModelV2::updateProperties() {
    
}

void FavoritesModelV2::parameterChanged(const String& parameterID, float newValue) {
    if(parameterID == getFavoritesIDParameterID().getParamID()) {
        // throttled by uiNeedsUpdate()
        _favoriteIDHost = static_cast<int>(newValue);
        uiNeedsUpdate(); // calls _tuningChangedUpdateUI() on a timer
    } else {
        // Assert false if the parameter ID does not match
        jassertfalse;
    }
}

void FavoritesModelV2::_tuningChangedUpdateUI() {
    // this callback should be called when the host has set _favoriteIDHost to the automated value
    if(_favoriteIDHost == -1) {
        jassertfalse;
        return;
    }
    
    const ScopedLock sl(_lock);
    auto const index = _rowNumberForID(_favoriteIDHost, DataList::Favorites);
    if(index == -1) {
        FavoritesComponentMessageBus::getInstance().broadcastMessage("Host recalled Favorite ID " + String(_favoriteIDHost) + " but it doesn't exist");
        _favoriteIDHost = -1; // reset for next time
    } else if (_favoriteRowNumber != index) {
        _favoriteRowNumber = index;
        _favoriteID = _favoriteIDHost;
        _favoriteIDHost = -1; // reset to unthrottle the next automated change
        _uiRecallFavoriteInternal(_favoriteRowNumber);
        FavoritesComponentMessageBus::getInstance().broadcastMessage(_status_message);
        _status_message = "";
    } else {
        DBG("_favoriteRowNumber == index == " + String(index));
    }
}

#pragma mark - uiAddFavorite

// stores current design's params, if its hash is unique
void FavoritesModelV2::uiAddNewFavorite
 (unsigned long design_index,
  String design_description, /* passed in based on _designsNames */
  unsigned long npo,
  String tuning_description,
  String tuning_param_description,
  StringArray parameter_keys,
  shared_ptr<Tuning> tuning) {
    // race
    if(_apvts == nullptr) {
        DBG("RACE: FavoritesModelV2::addFavorite called before _apvts is set");
        jassertfalse;
    }
    
    // lock
    const ScopedLock sl(_lock);
    
    // hash the params to determine if we have a dup
    auto parameters = new XmlElement("Parameters");
    
    // iterate through param keys and add them as children
    // also, create a human-readable description of the parameters
    String param_description = "";
    for(auto parameter_key : parameter_keys) {
        auto const parameter = _apvts->getParameter(parameter_key);
        auto const parameter_name = parameter->getName(50);
        auto const parameter_value_string = parameter->getCurrentValueAsText();
        param_description += parameter_name + ": " + parameter_value_string + "\n";

        auto const parameter_node = new XmlElement("Parameter");
        auto const parameter_value = static_cast<double>(*_apvts->getRawParameterValue(parameter_key));
        parameter_node->setAttribute(Identifier(parameter_key), parameter_value);
        parameters->addChildElement(parameter_node);
    }
    
    // lambda, for the AppTuningModel model params
    auto favATM = [&](auto condition, auto key) -> void {
        if(condition) {
            auto const parameter = _apvts->getParameter(key);
            auto const parameter_name = parameter->getName(50);
            auto const parameter_value_string = parameter->getCurrentValueAsText();
            param_description += parameter_name + ": " + parameter_value_string + "\n";

            auto const parameter_node = new XmlElement("Parameter");
            auto const parameter_value = static_cast<double>(*_apvts->getRawParameterValue(key));
            parameter_node->setAttribute(Identifier(key), parameter_value);
            parameters->addChildElement(parameter_node);
        }
    };
    
    favATM(_processor.restoreFavoritesStoreNPOOverride(), AppTuningModel::getAppTuningNPOOverrideEnableParameterID().getParamID());
    favATM(_processor.restoreFavoritesStoreNPOOverride(), AppTuningModel::getAppTuningNPOOverrideParameterID().getParamID());
    favATM(_processor.restoreFavoritesStorePeriodMiddleC(), AppTuningModel::getAppTuningOctaveMiddleCParameterID().getParamID());
    favATM(_processor.restoreFavoritesStoreNNMiddleC(), AppTuningModel::getAppTuningNoteNumberMiddleCParameterID().getParamID());
    favATM(_processor.restoreFavoritesStoreFrequencyMiddleC(), AppTuningModel::getAppTuningFrequencyMiddleCParameterID().getParamID());
    
    // create a hash for this favorite
    // whether this has design as a parameter doesn't matter because:
    // design params have at least one and have mutually exclusive keys
    auto const parametersString = parameters->toString();
    auto const hash_code = parametersString.hashCode(); // int, 32-bit
    bool dup_favorite = false; {
        for(auto data : _dataList->getChildIterator()) {
            auto data_hash = data->getIntAttribute("Parameter_Hash");
            if(hash_code == data_hash) {
                dup_favorite = true;
                break;
            }
        }
    }
    
    // duplicate tuning...NOP
    if(dup_favorite) {
        DBG("Duplicate favorite...NOP");
        FavoritesComponentMessageBus::getInstance().broadcastMessage("Can't add duplicate Favorite");
        delete parameters;
        return;
    }
    
    //        add_column(1, "ID", 50, 1, 0);
    //        add_column(2, "Icon", 50, 1, 0);
    //        add_column(3, "Design", 150, 1, 0);
    //        add_column(4, "NPO", 50, 1, 0);
    //        add_column(5, "Description", 250, 1, 1);
    //        add_column(6, "Parameters", 250, 1, 0);
    //        add_column(7, "Parameter_Hash", 250, 0, 0);
    
    // create new id
    auto const ID = _getNewID(); // locks
    if(ID == -1) {
        FavoritesComponentMessageBus::getInstance().broadcastMessage("INTERNAL ERROR: Can't add new Favorite because new ID can not be generated");
        delete parameters;
        return;
    }
    
    // new Favorite
    auto new_favorite = new XmlElement("FAVORITE");
    new_favorite->setAttribute("ID", ID);
    FavoritesIconRenderer::createFavoritesIconForHashcode(_processor, hash_code, tuning);
    auto const icon_url = "dont need data for this column";
    new_favorite->setAttribute("Icon", icon_url); // we actually don't need to store data for the icon column
    new_favorite->setAttribute("Design_Index", static_cast<int>(design_index));
    new_favorite->setAttribute("Design", design_description);
    new_favorite->setAttribute("NPO", static_cast<int>(npo));
    new_favorite->setAttribute("Description", tuning_description + "\n\n" + design_description + "\n\n" + param_description);
    new_favorite->setAttribute("Parameters", tuning_param_description + "\n\n" + param_description);
    new_favorite->setAttribute("Parameter_Hash", hash_code);
    new_favorite->addChildElement(parameters);
    _dataList->addChildElement(new_favorite);
    _writeFavoritesToDisk();
    uiSetFavoriteID(ID, "Created new Favorite ID: " + String(_favoriteID) + " at row: " + String(_favoriteRowNumber));
}

#pragma mark - uiRecallFavorite

void FavoritesModelV2::uiRecallFavoriteAtRowNumber(int favorite_index) {
    auto const ID = _IDForRowNumber(favorite_index, DataList::Favorites);
    if(ID != -1) {
        uiSetFavoriteID(ID, "Recalled Favorite ID: " + String(ID));
    } else {
        _status_message = "Can't find Favorite at index: " + String(favorite_index);
        FavoritesComponentMessageBus::getInstance().broadcastMessage(_status_message);
    }
}

// this actually recalls the favorite
void FavoritesModelV2::_uiRecallFavoriteInternal(int favorite_index) {
    // race
    if(_apvts == nullptr) {
        DBG("RACE: FavoritesModelV2::recallFavorite called before _apvts is set.");
        jassertfalse;
        return;
    }
    
    //
    const ScopedLock sl(_lock);
    auto const child = _dataList->getChildElement(favorite_index);
    if(child == nullptr) {
        DBG("FavoritesModelV2::recallFavorite: favorite_index not found: " + String(favorite_index));
        _status_message = "Can't find Favorite at index: " + String(favorite_index);
        FavoritesComponentMessageBus::getInstance().broadcastMessage(_status_message);
        return;
    }
    
    // grab attributes
    auto const ID = child->getIntAttribute("ID");
    auto const design_index = child->getIntAttribute("Design_Index");
    auto const parameters = child->getChildByName("Parameters");
    if(parameters == nullptr) {
        DBG("FavoritesModelV2::recallFavorite: parameters are null for favorite_index: " + String(favorite_index) + ", ID: " + String(ID));
        _status_message = "Internal Error: No params for Favorite at index: " + String(favorite_index);
        FavoritesComponentMessageBus::getInstance().broadcastMessage(_status_message);
        return;
    }
    if (parameters->getNumChildElements() == 0) {
        DBG("FavoritesModelV2::recallFavorite: parameters are empty for favorite_index: " + String(favorite_index) + ", ID: " + String(ID));
        _status_message = "Internal Error: No params for Favorite at index: " + String(favorite_index);
        FavoritesComponentMessageBus::getInstance().broadcastMessage(_status_message);
        return;
    }
    
    // iterate through parameters.
    // "PARAMETER" has only 1 attribute/value
    for(auto parameter : parameters->getChildIterator()) {
        auto const key = parameter->getAttributeName(0);
        jassert(key != String()); // empty string
        auto param = _apvts->getParameter(key);
        auto range = _apvts->getParameterRange(key);
        auto const value = static_cast<float>(parameter->getDoubleAttribute(key));
        auto const value01 = range.convertTo0to1(value);
        param->setValueNotifyingHost(value01);
    }
    
    // set the design(also calls setValueNotifyingHost)
    _processor.getDesignsModel()->favoritesSetDesign(static_cast<unsigned long>(design_index));
    
    // notify component to update ui
    sendActionMessage(getFavoritesModelV2UpdateUIMessage());
}

#pragma mark - uiDeleteFavoriteAtRow

void FavoritesModelV2::uiDeleteFavoriteAtRowNumber(int favorite_index) {
    // race
    if(_apvts == nullptr) {
        DBG("RACE: FavoritesModelV2::deleteFavoriteAtRow called before _apvts is set");
        jassertfalse;
    }
    
    const ScopedLock sl(_lock);
    auto const child = _dataList->getChildElement(favorite_index);
    if(child == nullptr) {
        DBG("FavoritesModelV2::deleteFavoriteAtRow: row not found:" + String(favorite_index));
        _status_message = "Cannot delete Favorite at row: " + String(favorite_index) + " because it cannot be found";
        FavoritesComponentMessageBus::getInstance().broadcastMessage(_status_message);
    } else {
        auto const ID = child->getIntAttribute("ID");
        auto const design_index = child->getIntAttribute("Design_Index");
        auto const isFavoritesDesignMorph = (design_index == _processor.getMorphModel()->ModelBase::getDesignIndex());
        _dataList->removeChildElement(child, true);
        
        // TODO:
        // how do you safely delete a Favorites icon?
        // it could be referred to by Morph favorites
        
        _writeFavoritesToDisk();
        
        // Deleting a morph favorite doesn't result in a stranded favorite
        if(!isFavoritesDesignMorph) {
            _performFavoritesIntegrityCheck();
        }
        
        //
        _status_message = "Deleted Favorite ID: " + String(ID) + ", at row: " + String(favorite_index);
        auto const num_rows = getNumRows(DataList::Favorites);
        if(num_rows == 0) {
            // nop
        } else if(num_rows == 1) {
            auto newID = _IDForRowNumber(0, DataList::Favorites);
            uiSetFavoriteID(newID, _status_message);
        } else {
            auto newIndex = clamp(_favoriteRowNumber - 1, 0, num_rows - 1);
            auto const newID = _IDForRowNumber(newIndex, DataList::Favorites);
            uiSetFavoriteID(newID, _status_message);
        }
    }
}

#pragma mark - uiRecallPreviousFavorite

void FavoritesModelV2::uiRecallPreviousFavorite() {
    auto const num_rows = getNumRows(DataList::Favorites);
    if(num_rows == 0) {
        _status_message = "No Favorites";
        FavoritesComponentMessageBus::getInstance().broadcastMessage(_status_message);
    } else if(num_rows == 1) {
        auto const ID = _IDForRowNumber(_favoriteRowNumber, DataList::Favorites);
        uiSetFavoriteID(ID);
    } else {
        auto const previous_row = (_favoriteRowNumber + num_rows - 1) % num_rows;
        auto const ID = _IDForRowNumber(previous_row, DataList::Favorites);
        uiSetFavoriteID(ID);
    }
}

#pragma mark - uiRecallNextFavorite

void FavoritesModelV2::uiRecallNextFavorite() {
    auto num_rows = getNumRows(DataList::Favorites);
    if(num_rows == 0) {
        _status_message = "No Favorites";
        FavoritesComponentMessageBus::getInstance().broadcastMessage(_status_message);
    } else if(num_rows == 1) {
        auto const ID = _IDForRowNumber(_favoriteRowNumber, DataList::Favorites);
        uiSetFavoriteID(ID);
    } else {
        auto const next_row = (_favoriteRowNumber + 1) % num_rows;
        auto const ID = _IDForRowNumber(next_row, DataList::Favorites);
        uiSetFavoriteID(ID);
    }
}

# pragma mark - UI

// needs additional info from DesignsModel but ultimately calls uiAddFavorite
void FavoritesModelV2::uiStoreCurrentTuningAsFavorite() {
    _processor.getDesignsModel()->uiStoreFavorite();
}

float FavoritesModelV2::uiGetFavoriteID() {
    auto const id = getFavoritesIDParameterID().getParamID();
    auto& param = *_apvts->getRawParameterValue(id);
    return param.load();
}

void FavoritesModelV2::uiSetFavoriteID(float ID, String status_message) {
    // Validate the ID parameter to ensure it's within range
    if (static_cast<int>(ID) < FavoritesModelV2::getFavoritesMinID() || static_cast<int>(ID) > FavoritesModelV2::getFavoritesMaxID()) {
        DBG("FavoritesModelV2::setFavoriteID: ID out of range: " + String(ID));
        _status_message = "INTERNAL ERROR: Favorite ID out of range: " + String(ID);
        FavoritesComponentMessageBus::getInstance().broadcastMessage(_status_message);
        jassertfalse;
        return;
    }
    // race
    if(_apvts == nullptr) {
        DBG("RACE: FavoritesModelV2::setFavoriteID called before _apvts is set");
        jassertfalse;
    }
    
    _status_message = (_status_message == "") ? "Recalled Favorite ID: " + String(ID) : status_message;
    auto key = getFavoritesIDParameterID().getParamID();
    auto param = _apvts->getParameter(key);
    auto range = _apvts->getParameterRange(key);
    auto const value01 = range.convertTo0to1(ID);
    param->setValueNotifyingHost(value01);
}

#pragma mark - id/index helpers

Favorite FavoritesModelV2::_getFavoriteForID(int ID) {
    // race
    if(_apvts == nullptr) {
        DBG("RACE: FavoritesModelV2::getFavoriteForID called before _apvts is set");
        jassertfalse;
    }
    
    // range
    jassert(ID >= FavoritesModelV2::getFavoritesMinID());
    jassert(ID <= FavoritesModelV2::getFavoritesMaxID());
    
    const ScopedLock sl(_lock);
    for(auto data : _dataList->getChildIterator()) {
        // create a Favorite object
        auto childID = data->getIntAttribute("ID");
        if(childID == ID) {
            auto data_hash = data->getIntAttribute("Parameter_Hash");
            auto iconImageURL = FavoritesIconRenderer::getFavoritesIconImageForHashcode(data_hash);
            jassert(iconImageURL != nullptr);
            auto designIndex = data->getIntAttribute("Design_Index");
            auto designDescription = data->getStringAttribute("Description");
            auto NPO = data->getIntAttribute("NPO");
            auto tuningDescription = data->getStringAttribute("Description");
            auto const parameters = data->getChildByName("Parameters");
            if(parameters == nullptr) {
                DBG("FavoritesModelV2::getFavoriteForID: parameters are null for ID: " + String(ID));
                _status_message = "INTERNAL ERROR: parameters null for Favorite ID: " + String(ID);
                FavoritesComponentMessageBus::getInstance().broadcastMessage(_status_message);
                jassertfalse;
                return Favorite();
            }
            // iterate through parameters.
            vector<FavoriteParam01> params;
            for(auto parameter : parameters->getChildIterator()) {
                auto const key = parameter->getAttributeName(0);
                jassert(key != String()); // empty string
                auto const value = static_cast<float>(parameter->getDoubleAttribute(key));
                auto f01 = FavoriteParam01(key, value);
                params.push_back(f01);
            }
            // the Favorite representation
            auto f = Favorite(ID, iconImageURL, designIndex, designDescription, NPO, tuningDescription, params);
            return f;
        }
    }
    
    // TODO: Make this return preset 12ET
    DBG("FavoritesModelV2::getFavoriteForID can't find ID: " + String(ID));
    _status_message = "FATAL: Can't find Favorite for ID: " + String(ID) + ", defaulting to 12ET";
    FavoritesComponentMessageBus::getInstance().broadcastMessage(_status_message);
    jassertfalse;
    return Favorite();
}

int FavoritesModelV2::_IDForRowNumber(int rowNumber, DataList dataList) {
    // race
    if(_apvts == nullptr) {
        DBG("RACE: FavoritesModelV2::getFavoriteForID called before _apvts is set");
        jassertfalse;
    }
    
    const ScopedLock sl(_lock);
    XmlElement* child = nullptr;
    switch(dataList) {
        case DataList::Favorites:
            child = _dataList->getChildElement(rowNumber);
            break;
        case DataList::FavoritesA:
            child = _dataListA->getChildElement(rowNumber);
            break;
        case DataList::FavoritesB:
            child = _dataListB->getChildElement(rowNumber);
            break;
        default:
            jassertfalse;
    }
    
    if(child == nullptr) {
        DBG("FavoritesModelV2::IDForRowNumber: rowNumber not found: " + String(rowNumber));
        jassertfalse;
        return -1;
    } else {
        auto const ID = child->getIntAttribute("ID");
        jassert(ID >= FavoritesModelV2::getFavoritesMinID());
        jassert(ID <= FavoritesModelV2::getFavoritesMaxID());
        return ID;
    }
}

int FavoritesModelV2::_rowNumberForID(int ID, DataList dataList) {
    // race
    if(_apvts == nullptr) {
        DBG("RACE: FavoritesModelV2::getFavoriteForID called before _apvts is set");
        jassertfalse;
    }
    
    // range
    jassert(ID >= FavoritesModelV2::getFavoritesMinID());
    jassert(ID <= FavoritesModelV2::getFavoritesMaxID());
    
    // lock
    const ScopedLock sl(_lock);
    
    int row = 0;
    switch(dataList) {
        case DataList::Favorites:
            for(auto data : _dataList->getChildIterator()) {
                // create a Favorite object
                auto childID = data->getIntAttribute("ID");
                if(childID == ID) {
                    return row;
                }
                row++;
            }
            break;
        case DataList::FavoritesA:
            for(auto data : _dataListA->getChildIterator()) {
                // create a Favorite object
                auto childID = data->getIntAttribute("ID");
                if(childID == ID) {
                    return row;
                }
                row++;
            }
            break;
        case DataList::FavoritesB:
            for(auto data : _dataListB->getChildIterator()) {
                // create a Favorite object
                auto childID = data->getIntAttribute("ID");
                if(childID == ID) {
                    return row;
                }
                row++;
            }
            break;
        default:
            jassertfalse;
    }
    
    // TODO: if ID is not found is it fatal?
    return -1;
}

#pragma mark - _getFavoritesLibraryFile

File FavoritesModelV2::_getFavoritesLibraryFile() {
    // ~/Library/WilsonicMTSESP/Favorites_00_v2.xml
    File favorites_library = WilsonicProcessor::appLibraryDir().getChildFile("Favorites_00_v2.xml");
    return favorites_library;
}

#pragma mark - _writeFavoritesToDisk

bool FavoritesModelV2::_writeFavoritesToDisk() {
    const ScopedLock sl(_lock);
    
    // keep _dataListA/B in sync (before saving)
    jassert(_dataList != nullptr);
    _dataListA = _getDataListNonMorph();
    _dataListB = _getDataListNonMorph();
    
    // must be a valid favorites library
    jassert(_favoritesLibrary != nullptr);
    auto fl = _favoritesLibrary->toString();
    
    // TODO: replace this with writeTo
    auto file = _getFavoritesLibraryFile();
    auto success = file.replaceWithText(fl);
    if(!success) {
        FavoritesComponentMessageBus::getInstance().broadcastMessage("FATAL ERROR: Can NOT write Favorites file to disk");
    }
    jassert(success == true); // for now this is fatal
    
    // debug
    //_logXML();
    return success;
}

#pragma mark - _logFavoritesXML

void FavoritesModelV2::_logXML() {
    const ScopedLock sl(_lock);
    
    // default
    auto root_as_xml = _favoritesLibrary->toString();
    DBG("DEBUG: favorites library as xml string:");
    DBG(root_as_xml);
    DBG("");
}

#pragma mark - _getAttributeNameForColumnId

String FavoritesModelV2::_getAttributeNameForColumnId(const int columnId) const {
    const ScopedLock sl(_lock);
    for(auto* columnXml : _columnList->getChildIterator()) {
        if(columnXml->getIntAttribute("columnId") == columnId) {
            return columnXml->getStringAttribute("name");
        }
    }
    return {};
}

#pragma mark - ActionListener

// ActionListener
void FavoritesModelV2::actionListenerCallback(const String& message) {
    if(message == ScalaModel::getScalaUserFileWasDeleted()) {
        auto const success = _performUserScalaIntegrityCheck();
        if(success) {
            _performFavoritesIntegrityCheck();
            sendActionMessage(getFavoritesModelV2UpdateUIMessage());
        }
    } else if (message == DesignsModel::getScalaTuningChangedActionMessage()) {
        // NOP for FavoritesModel
    } else {
        jassertfalse;
    }
}

#pragma mark - TableListBoxModel

int FavoritesModelV2::getNumRows(DataList dataList) {
    const ScopedLock sl(_lock);
    // get num rows
    switch(dataList) {
        case DataList::Favorites:
            return _dataList->getNumChildElements();
            break;
        case DataList::FavoritesA:
            return _dataListA->getNumChildElements();
            break;
        case DataList::FavoritesB:
            return _dataListB->getNumChildElements();            
            break;
        default:
            jassertfalse;
    }
    jassertfalse;
    return -1;
}

int FavoritesModelV2::getColumnAutoSizeWidth(int columnId) {
    const ScopedLock sl(_lock);
    auto widest = FavoritesIconRenderer::icon_dimension;
    for(auto i = getNumRows(DataList::Favorites); --i >= 0;) {
        if(i == 2) {
            // icon
            return widest;
        } else if(auto* rowElement = _dataList->getChildElement(i)) {
            auto text = rowElement->getStringAttribute(_getAttributeNameForColumnId(columnId));
            widest = jmax(widest, GlyphArrangement::getStringWidthInt(_font, text));
        }
    }
    return widest;
}

void FavoritesModelV2::sortOrderChanged(int newSortColumnId, bool isForwards, DataList dataList) {
    if(newSortColumnId == 2) {
        // don't sort by id, nor icon
        return;
    }
    bool can_sort = false;
    for(auto c : _columns) {
        // doesn't mutate, so no lock
        if(c.columnId == newSortColumnId && c.sortable == 1) {
            can_sort = true;
            break;
        }
    }
    if(!can_sort) {
        return;
    }
    const ScopedLock sl(_lock);
    // sort
    // TODO: save newSortColumnId for each DataList type
    FavoritesDataSorter sorter(_getAttributeNameForColumnId(newSortColumnId), isForwards);
    switch(dataList) {
        case DataList::Favorites:
            _dataList->sortChildElements(sorter);
            break;
        case DataList::FavoritesA:
            _dataListA->sortChildElements(sorter);
            break;
        case DataList::FavoritesB:
            _dataListB->sortChildElements(sorter);
            break;
        default:
            jassertfalse;
    }
}

# pragma mark - private helpers

bool FavoritesModelV2::_deleteFavoriteID(int favoritesID) {
    // race
    if(_apvts == nullptr) {
        DBG("RACE: FavoritesModelV2::_deleteFavoriteID called before _apvts is set");
        jassertfalse;
    }
    
    // range
    jassert(favoritesID >= FavoritesModelV2::getFavoritesMinID());
    jassert(favoritesID <= FavoritesModelV2::getFavoritesMaxID());
    
    const ScopedLock sl(_lock);
    for(auto data : _dataList->getChildIterator()) {
        auto const ID = data->getIntAttribute("ID");
        if(ID == favoritesID) {
            DBG("FavoritesModelV2::_deleteFavoriteID: deleting favoritesID:" + String(favoritesID));
            _dataList->removeChildElement(data, true);
            _writeFavoritesToDisk();
            _favoriteRowNumber = -1;
            _favoriteID = -1;
            return true;
        }
    }
    DBG("FavoritesModelV2::_deleteFavoriteID: favoriteID not found:" + String(favoritesID));
    return false;
}

// private helper does not update ui
bool FavoritesModelV2::_performUserScalaIntegrityCheck() {
    const ScopedLock sl(_lock);
    
    // map of only valid user scala file IDs
    auto const integrity = _processor.getScalaModel()->getIntegrityCheck();
    
    // Collect all Favorite IDs that refer to a missing User Scala File ID
    vector<int> invalid_IDs;
    for(auto data : _dataList->getChildIterator()) {
        auto const favorite_ID = data->getIntAttribute("ID");
        
        // Is this a Scala Favorite?
        auto const design_index = data->getIntAttribute("Design_Index");
        if(design_index == _processor.getScalaModel()->getDesignIndex()) {
            // if so get it's parameters
            auto const parameters = data->getChildByName("Parameters");
            if(parameters == nullptr) {
                jassertfalse;
                continue;
            }
            
            // iterate through parameters for user scala file id
            bool isFavoriteUserScala = false;
            int favoriteUserScalaID = -1;
            for(auto parameter : parameters->getChildIterator()) {
                auto const parameterKey = parameter->getAttributeName(0);
                jassert(parameterKey != String()); // empty string
                auto const parameterValue = parameter->getIntAttribute(parameterKey);
                if(parameterKey == ScalaModel::getScalaLibraryParameterID().getParamID()) {
                    if(parameterValue == ScalaModel::Library::User) {
                        isFavoriteUserScala = true;
                    }
                } else if(parameterKey == ScalaModel::getScalaUserTuningIDParameterID().getParamID()) {
                    favoriteUserScalaID = parameterValue;
                }
            }
            
            // if a user scala id is not in integrity, add it to list
            if(isFavoriteUserScala && favoriteUserScalaID != -1) {
                auto it = integrity.find(favoriteUserScalaID);
                if(it == integrity.end()) {
                    invalid_IDs.push_back(favorite_ID);
                    DBG("FavoritesModelV2::performUserScalaIntegrityCheck(): Need to delete Scala Favorite ID:" + String(favorite_ID) + " because it refers to missing Scala ID: " + String(favoriteUserScalaID));
                }
            }
        }
    }
    
    // delete favorite
    bool didDeleteFavorite = false;
    for(int deleteID : invalid_IDs) {
        // should be just 1 id
        auto const result = _deleteFavoriteID(deleteID);
        if(result)  {
            didDeleteFavorite = true; // OR
            FavoritesComponentMessageBus::getInstance().broadcastMessage("Deleted Favorite User Scala ID: " + String(deleteID));
        }
    }
    return didDeleteFavorite;
}

bool FavoritesModelV2::_performFavoritesIntegrityCheck() {
    const ScopedLock sl(_lock);
    
    // map of valid Favorite non-morph IDs
    auto const integrity = _getNonMorphIntegrityCheck();
    
    // Collect Morph Favorite ID's that refer to a missing A ID, or B ID (i.e., referring to the Favorite that referred to a deleted Scala file)
    unordered_map<int, int> ids;
    for(auto data : _dataList->getChildIterator()) {
        auto const ID = data->getIntAttribute("ID");
        
        // Is this a Morph Favorite?
        auto const design_index = data->getIntAttribute("Design_Index");
        if(design_index == _processor.getMorphModel()->getDesignIndex()) {
            // if so get it's parameters
            auto const parameters = data->getChildByName("Parameters");
            if(parameters == nullptr) {
                jassertfalse;
                continue;
            }
            
            // iterate through parameters for both A and B IDs
            int has_A_ID = -1;
            int has_B_ID = -1;
            for(auto parameter : parameters->getChildIterator()) {
                auto const key = parameter->getAttributeName(0);
                jassert(key != String()); // empty string
                auto const param = parameter->getIntAttribute(key);
                if(key == MorphModel::getMorphFavoriteAParameterID().getParamID()) {
                    has_A_ID = param;
                } else if(key == MorphModel::getMorphFavoriteBParameterID().getParamID()) {
                    has_B_ID = param;
                }
            }
            jassert(has_A_ID != -1 && has_B_ID != -1);
            
            // A
            {
                // delete Morph ID if it refers to deleted A_ID
                auto it = integrity.find(has_A_ID);
                if(it == integrity.end()) {
                    ids[ID] = ID; // fine if clobbers
                    DBG("FavoritesModelV2::_performMorphIntegrityCheck(): Need to delete Favorite Morph ID:" + String(ID) + " because A ID refers to missing Favorite ID: " + String(has_A_ID));
                }
            }
            
            // B
            {
                // delete Morph ID if it refers to deleted B_ID
                auto it = integrity.find(has_B_ID);
                if(it == integrity.end()) {
                    ids[ID] = ID; // fine if clobbers
                    DBG("FavoritesModelV2::_performMorphIntegrityCheck(): Need to delete Favorite Morph ID:" + String(ID) + " because B ID refers to missing Favorite ID: " + String(has_B_ID));
                }
            }
        }
    }
    
    // delete the morph favorite ids that refer to missing favorite ids
    bool didDeleteFavorite = false;
    for(const auto& pair : ids) {
        auto const favoriteID = pair.first;
        auto const result = _deleteFavoriteID(favoriteID);
        if(result) {
            didDeleteFavorite = true; // like an "or" for return value
            FavoritesComponentMessageBus::getInstance().broadcastMessage("Deleted Favorite Morph ID: " + String(favoriteID));
        }
    }
    return didDeleteFavorite;
}

// return the first available id
int FavoritesModelV2::_getNewID() {
    const ScopedLock sl(_lock);
    
    // Collect all IDs into a vector
    vector<int> ids;
    for(auto data : _dataList->getChildIterator()) {
        ids.push_back(data->getIntAttribute("ID"));
    }
    
    // Sort the vector of IDs
    sort(ids.begin(), ids.end());
    
    // Find the first available ID
    int newID = getFavoritesMinID();
    for(int id : ids) {
        if(id == newID) {
            newID++;
        } else if(id > newID) {
            break; // Found a gap
        }
    }
    if(newID > getFavoritesMaxID()) {
        return -1; // Or handle the error as appropriate
    }
    return newID;
}

Font FavoritesModelV2::getFont() {
    return _font;
}

String FavoritesModelV2::getText(int rowNumber, int columnId, DataList dataList) {
    const ScopedLock sl(_lock);
    switch(dataList) {
        case DataList::Favorites:
            if(auto* rowElement = _dataList->getChildElement(rowNumber)) {
                auto text = rowElement->getStringAttribute(_getAttributeNameForColumnId(columnId));
                return text;
            }
            break;
        case DataList::FavoritesA:
            if(auto* rowElementA = _dataListA->getChildElement(rowNumber)) {
                auto text = rowElementA->getStringAttribute(_getAttributeNameForColumnId(columnId));
                return text;
            }
            break;
        case DataList::FavoritesB:
            if(auto* rowElementB = _dataListB->getChildElement(rowNumber)) {
                auto text = rowElementB->getStringAttribute(_getAttributeNameForColumnId(columnId));
                return text;
            }
            break;
        default:
            jassertfalse;
    }
    
    return {};
}

void FavoritesModelV2::setText(String columnName, const int rowNumber, const String& newText) {
    const ScopedLock sl(_lock);
    
    // set text
    _dataList->getChildElement(rowNumber)->setAttribute(columnName, newText);
    
    // store on disk
    _writeFavoritesToDisk();
}

int FavoritesModelV2::getSelection(const int rowNumber, DataList dataList) const {
    const ScopedLock sl(_lock);
    
    // get selection
    switch(dataList) {
        case DataList::Favorites:
            return _dataList->getChildElement(rowNumber)->getIntAttribute("Select");
            break;
        case DataList::FavoritesA:
            return _dataListA->getChildElement(rowNumber)->getIntAttribute("Select");
            break;
        case DataList::FavoritesB:
            return _dataListB->getChildElement(rowNumber)->getIntAttribute("Select");
            break;
        default:
            jassertfalse;
    }
    jassertfalse;
    return -1;
}

void FavoritesModelV2::setSelection(const int rowNumber, const int newSelection, DataList dataList) {
    const ScopedLock sl(_lock);
    
    // set selection
    switch(dataList) {
        case DataList::Favorites:
            // clear all selections
            for(auto data : _dataList->getChildIterator()) {
                data->setAttribute("Select", 0);
            }
            
            // select
            _dataList->getChildElement(rowNumber)->setAttribute("Select", newSelection);
            break;
        case DataList::FavoritesA:
            // clear all selections
            for(auto data : _dataListA->getChildIterator()) {
                data->setAttribute("Select", 0);
            }
            
            // select
            _dataListA->getChildElement(rowNumber)->setAttribute("Select", newSelection);
            break;
        case DataList::FavoritesB:
            // clear all selections
            for(auto data : _dataListB->getChildIterator()) {
                data->setAttribute("Select", 0);
            }
            
            // select
            _dataListB->getChildElement(rowNumber)->setAttribute("Select", newSelection);
            break;
        default:
            jassertfalse;
    }
}

int FavoritesModelV2::getFavoriteRowNumber(DataList dataList) {
    auto const mm = _processor.getMorphModel();
    switch(dataList) {
        case DataList::Favorites: {
            return _favoriteRowNumber;
            break;
        }
        case DataList::FavoritesA:
        {
            auto const IDa = mm->uiGetID_A();
            auto const rowNumber = _rowNumberForID(IDa, DataList::FavoritesA);
            return rowNumber;
            break;
        }
        case DataList::FavoritesB:
        {
            auto const IDb = mm->uiGetID_B();
            auto const rowNumber = _rowNumberForID(IDb, DataList::FavoritesB);
            return rowNumber;
            break;
        }
        default:
            jassertfalse;
    }
}

vector<Columns> FavoritesModelV2::getColumns() {
    return _columns;
}

shared_ptr<Image> FavoritesModelV2::getIcon(int rowNumber, DataList dataList) {
    const ScopedLock sl(_lock);
    int hash_code = 0;
    
    // get hash
    switch(dataList) {
        case DataList::Favorites:
            hash_code = _dataList->getChildElement(rowNumber)->getIntAttribute("Parameter_Hash");
            break;
        case DataList::FavoritesA:
            hash_code = _dataListA->getChildElement(rowNumber)->getIntAttribute("Parameter_Hash");
            break;
        case DataList::FavoritesB:
            hash_code = _dataListB->getChildElement(rowNumber)->getIntAttribute("Parameter_Hash");
            break;
        default:
            jassertfalse;
    }
    
    // get ptr to Image
    auto img_ptr = FavoritesIconRenderer::getFavoritesIconImageForHashcode(hash_code);
    
    // TODO: return a default icon? YES
    return img_ptr;
}

unique_ptr<XmlElement> FavoritesModelV2::_getDataListNonMorph() {
    const ScopedLock sl(_lock);
    
    if (_dataList == nullptr) {
        return nullptr;
    }
    
    auto nonMorphChildren = make_unique<XmlElement>(_dataList->getTagName());
    for(auto* child : _dataList->getChildIterator()) {
        if(child->getIntAttribute("Design_Index") != 11) {
            // Deep copy the child and add it to the filtered root
            nonMorphChildren->addChildElement(new XmlElement(*child));
        }
    }
    return nonMorphChildren;
}

unordered_map<int, int> FavoritesModelV2::_getNonMorphIntegrityCheck() {
    const ScopedLock sl(_lock);
        
    // assert on duplicates
    unordered_map<int, int> integrity {};
    auto dataList = _getDataListNonMorph();
    for(auto data : dataList->getChildIterator()) {
        auto const ID = data->getIntAttribute("ID");
        jassert(ID >= FavoritesModelV2::getFavoritesMinID());
        jassert(ID <= FavoritesModelV2::getFavoritesMaxID());
        auto it = integrity.find(ID);
        if(it == integrity.end()) {
            integrity[ID] = ID;
        } else {
            // we should not have duplicate/invalid IDs
            DBG("Duplicate/Invalid Favorite non-morph ID found: " + String(ID));
            jassertfalse;
        }
    }
    return integrity;
}
