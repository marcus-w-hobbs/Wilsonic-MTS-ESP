/*
 ==============================================================================
 
 ScalaBundleModel.cpp
 Created: 3 Apr 2023 8:36:36pm
 Author:  Marcus W. Hobbs
 
 ==============================================================================
 */

#include "ScalaBundleModel.h"
#include "ScalaComponentMessageBus.h"
#include "ScalaModel.h"

ScalaBundleModel::ScalaBundleModel(File iconCacheDirectory)
: _iconCacheDirectory(iconCacheDirectory) // File(String&)
{
    // read bundled library xml from BinaryData
    auto data = BinaryData::scala_bundle_00_v0_xml;
    auto data_size = BinaryData::scala_bundle_00_v0_xmlSize;
    //TODO: does this need to be UTF8?  see String class docs
    String xmlContent(data, (size_t)data_size);
    XmlDocument xmlDoc(xmlContent);
    _scalaLibrary = xmlDoc.getDocumentElement();
    
    // must be a valid favorites library
    jassert(_scalaLibrary != nullptr);
    _dataList = _scalaLibrary->getChildByName ("DATA");
    jassert(_dataList != nullptr);
    _columnList = _scalaLibrary->getChildByName ("COLUMNS");
    jassert(_columnList != nullptr);
    
    // visible columns have these flags:
    auto const visibleFlag =
    TableHeaderComponent::visible |
    TableHeaderComponent::resizable |
    TableHeaderComponent::draggable |
    TableHeaderComponent::resizable |
    TableHeaderComponent::appearsOnColumnMenu |
    TableHeaderComponent::sortable;
    for(auto* columnXml : _columnList->getChildIterator())
    {
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
    //_logXML();
}


// public methods

// nop if ID does not exist
shared_ptr<ScalaTuningImp> ScalaBundleModel::getScalaTuningForID(int ID)
{
    shared_ptr<ScalaTuningImp> retVal = nullptr;
    auto const row = _getRowForID(ID);
    if(row != -1)
    {
        //DBG ("ScalaBundleModel::getScalaTuningForID:" + String(ID) + ", row calculated:" + String(row));
        retVal = getScalaTuningForRow(row);
    }
    else
    {
        jassertfalse;
    }
    
    return retVal;
}

// nullptr is row is out of range
shared_ptr<ScalaTuningImp> ScalaBundleModel::getScalaTuningForRow(int row_number)
{
    // xml is read-only, so no lock required
    
    //DBG ("ScalaBundleModel::getScalaTuningForRow: row: " + String(row_number));
    
    // get scala file text from column 8
    auto scl_text = getText(row_number, 8);
    auto scala_tuning = ScalaTuningImp::createScalaTuningFromSclString(scl_text);
    if(scala_tuning == nullptr)
    {
        DBG ("ScalaBundleModel::getScalaTuningForRow: row: " + String(row_number) + ": FATAL...can't parse file");
        jassertfalse;
    }
    
    // this code duplicated from ScalaUserModel
    
    // create icon if necessary
    auto scl_file_name = _getIconFilename(row_number); // icon file name same as .scl
    auto icon_file = _fullPathToIconFile(scl_file_name);
    auto image = ImageFileFormat::loadFrom(icon_file);
    if (!image.isValid())
    {
        //DBG ("ScalaBundleModel::getScalaTuningForRow: icon does not exist for: " + scl_file_name);
        
        // create bounds for icon
        auto dim = ScalaIconRenderer::icon_dimension_render;
        auto const bounds = Rectangle<int>(0, 0, dim, dim);
        
        // create image
        Image icon_image(Image::ARGB, dim, dim, true);
        
        // create graphics context from image
        Graphics g(icon_image);
        
        // paint pitch wheel onto graphics context
        ScalaIconRenderer::paintPitchWheel(g, scala_tuning, bounds);
        
        // file output stream
        FileOutputStream fstream(icon_file);
        
        // write png
        PNGImageFormat png_writer;
        auto const success = png_writer.writeImageToStream(icon_image, fstream);
        
        // successful?
        if (!success)
        {
            DBG("ScalaBundleModel::getScalaTuningForRow: " + String(row_number) + "Error writing icon: " + icon_file.getFullPathName());
            jassertfalse;
        }
    }
        
    // selection state
    auto const ID = _getIDForRow(row_number);
    if(ID >= ScalaModel::getScalaBundledMinID() && ID <= ScalaModel::getScalaBundledMaxID())
    {
        _selectedID = ID;
        selectRow(row_number);
    }
    else
    {
        DBG ("ScalaBundleModel::getScalaTuningForRow: ID for row failed!");
        ScalaComponentMessageBus::getInstance().broadcastMessage("Internal Error: Can not get ID for row: " + String(row_number));
        jassertfalse;
    }
    
    return scala_tuning;
}

// this code duplicated from ScalaUserModel
shared_ptr<ScalaTuningImp> ScalaBundleModel::recallPreviousScala()
{
    // lock
    const ScopedLock sl(_lock);
    
    // valid selectedID and row?
    auto const num_rows = getNumRows();
    auto row = _getRowForID(_selectedID);
    if(row < 0 || getNumRows() < 1)
    {
        DBG ("ScalaBundleModel::recallPreviousScala: _getRowForID _selectedID = -1");
        jassertfalse;
        return nullptr;
    }
    
    if(num_rows > 1)
    {
        row = (row - 1 + num_rows) % num_rows; // Corrected calculation ChatGPT4
    }
    else
    {
        row = 0;
    }
    
    return getScalaTuningForRow(row); // sets _selectedID
}

// this code duplicated from ScalaUserModel
shared_ptr<ScalaTuningImp> ScalaBundleModel::recallNextScala()
{
    // lock
    const ScopedLock sl(_lock);
    
    // valid selectedID and row?
    auto const num_rows = getNumRows();
    auto row = _getRowForID(_selectedID);
    if(row < 0) // bundle has constant number of entries > 0
    {
        DBG("ScalaBundleModel::recallPreviousScala: _getRowForID _selectedID = -1");
        row = 0;
    }
    
    if(num_rows > 1)
    {
        row = (row + 1) % num_rows; // Corrected calculation ChatGPT4
    }
    else
    {
        row = 0;
    }
    
    return getScalaTuningForRow(row); // sets _selectedID
}

// this code duplicated from ScalaUserModel
int ScalaBundleModel::getSelectedRowNumber()
{
    auto const retVal = _getRowForID(_selectedID);
    //DBG ("ScalaBundleModel::getSelectedRowNumber: _selectedID: " + String(_selectedID) + ", selected row number: " + String(retVal));
    
    return retVal;
}

int ScalaBundleModel::getSelectedID()
{
    return _selectedID;
}

// unused...you can't delete a bundled scala file
unordered_map<int, int> ScalaBundleModel::getIntegrityCheck()
{
    jassertfalse;
    return unordered_map<int, int> {};
}

#pragma mark - TableListBoxModel

// this code duplicated from ScalaUserModel
int ScalaBundleModel::getNumRows()
{
    // lock
    const ScopedLock sl(_lock);
    
    return _scalaLibrary->getChildByName("DATA")->getNumChildElements();
}

// this code duplicated from ScalaUserModel
int ScalaBundleModel::getColumnAutoSizeWidth(int columnId)
{
    // lock
    const ScopedLock sl(_lock);
    
    auto widest = FavoritesIconRenderer::icon_dimension;
    for(auto i = getNumRows(); --i >= 0;)
    {
        if(i == 2) // icon
        {
            return widest;
        }
        else if(auto* rowElement = _dataList->getChildElement(i))
        {
            auto text = rowElement->getStringAttribute(_getAttributeNameForColumnId(columnId));
            widest = jmax(widest, GlyphArrangement::getStringWidthInt(_font, text));
        }
    }
    
    return widest;
}

// this code duplicated from ScalaUserModel
void ScalaBundleModel::sortOrderChanged(int new_sort_column_id, bool is_forwards)
{
    if(new_sort_column_id == 2) // don't sort by icon
    {
        return;
    }
    
    bool can_sort = false;
    for(auto c : _columns) // doesn't mutate, so no lock
    {
        if(c.columnId == new_sort_column_id && c.sortable == 1)
        {
            can_sort = true;
            break;
        }
    }
    
    if (! can_sort)
    {
        return;
    }
    
    // lock
    const ScopedLock sl(_lock);
    
    // sort
    ScalaLibraryDataSorter sorter(_getAttributeNameForColumnId(new_sort_column_id), is_forwards);
    _dataList->sortChildElements(sorter);
}

// this code duplicated from ScalaUserModel
String ScalaBundleModel::getText(int rowNumber, int columnId)
{
    // lock
    const ScopedLock sl(_lock);
    
    //
    if(auto* rowElement = _dataList->getChildElement(rowNumber))
    {
        auto text = rowElement->getStringAttribute(_getAttributeNameForColumnId(columnId));
        
        return text;
    }
    
    return {};
}

// this code duplicated from ScalaUserModel
int ScalaBundleModel::getIsSelectedForRow(const int rowNumber) const
{
    // lock
    const ScopedLock sl(_lock);
    
    // get selection
    return _dataList->getChildElement(rowNumber)->getIntAttribute ("Select");
}

// this code duplicated from ScalaUserModel
void ScalaBundleModel::selectRow(const int rowNumber)
{
    // lock
    const ScopedLock sl(_lock);
    
    //DBG ("ScalaUserModel::setSelection: (" + String(rowNumber) + ")");
    
    // can only select one item...if selecting this row: de-select all others and update _selectedID
    for(auto data : _dataList->getChildIterator())
    {
        data->setAttribute("Select", 0);
    }
    
    // select
    _dataList->getChildElement(rowNumber)->setAttribute("Select", 1);
}

// this code duplicated from ScalaUserModel
shared_ptr<Image> ScalaBundleModel::getIcon(int row_number)
{
    // get icon if it exists
    auto icon_name = _getIconFilename(row_number);
    auto icon_file = _fullPathToIconFile(icon_name);
    if (! icon_file.existsAsFile())
    {
        // inefficient reuse of file import's creation of icon
        auto lazy_way_to_make_an_icon = getScalaTuningForRow(row_number);
        jassert(lazy_way_to_make_an_icon != nullptr);
    }
    
    // should be valid now
    auto image = ImageFileFormat::loadFrom(icon_file);
    if (! image.isValid())
    {
        jassertfalse;
    }
    
    return make_shared<Image>(std::move(image));
}

#pragma mark - private methods

// this code duplicated from ScalaUserModel
// icons are lazily created so they may not exist.
File ScalaBundleModel::_fullPathToIconFile(String file_name)
{
    auto full_path = File(_iconCacheDirectory.getFullPathName() + "/" + file_name);
    
    return full_path;
}

// this code duplicated from ScalaUserModel
String ScalaBundleModel::_getIconFilename(int rowNumber)
{
    return getText(rowNumber, 3);  // id 3 is scala filename
}

// this code duplicated from ScalaUserModel
void ScalaBundleModel::_logXML()
{
    // lock
    const ScopedLock sl(_lock);
    
    // default
    auto root_as_xml = _scalaLibrary->toString();
    DBG("ScalaBundleModel::_logXML: scala bundle library as xml string:");
    DBG(root_as_xml);
    DBG("");
}

// this code duplicated from ScalaUserModel
String ScalaBundleModel::_getAttributeNameForColumnId(const int columnId) const
{
    // lock
    const ScopedLock sl(_lock);
    
    for(auto* columnXml : _columnList->getChildIterator())
    {
        if(columnXml->getIntAttribute ("columnId") == columnId)
            return columnXml->getStringAttribute ("name");
    }
    
    return {};
}

// this code duplicated from ScalaUserModel
int ScalaBundleModel::_getIDForRow(int row_number)
{
    // lock
    const ScopedLock sl(_lock);
    
    int row = 0;
    for(auto data : _dataList->getChildIterator())
    {
        if(row == row_number)
        {
            auto id_number = data->getIntAttribute("ID");
            return id_number;
        }
        row++;
    }
    
    // if you get here it's because you asked for an id that does not exist
    jassertfalse;
    return -1;
}

// this code duplicated from ScalaUserModel
int ScalaBundleModel::_getRowForID(int id_number)
{
    // lock
    const ScopedLock sl(_lock);
    
    int row = 0;
    for(auto data : _dataList->getChildIterator())
    {
        auto id_row = data->getIntAttribute("ID");
        if(id_row == id_number)
        {
            return row;
        }
        row++;
    }
    
    // if you get here it's because you asked for an id that doesn't exist in _dataList
    return -1;
}
