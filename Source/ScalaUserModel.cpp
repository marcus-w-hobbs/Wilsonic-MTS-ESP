/*
 ==============================================================================
 
 ScalaUserModel.cpp
 Created: 15 Oct 2022 2:19:29pm
 Author:  Marcus W. Hobbs
 
 ==============================================================================
 */

#include "ScalaUserModel.h"
#include "ScalaComponentMessageBus.h"
#include "ScalaModel.h"

#pragma mark - lifecycle

ScalaUserModel::ScalaUserModel(File xmlFile, File scalaFileDirectory, File iconCacheDirectory)
: _xmlFile(xmlFile)
, _scalaFileDirectory(scalaFileDirectory) // File(String&)
, _iconCacheDirectory(iconCacheDirectory) // File(String&)
{
    // null or empty file...Create and Save
    if(_xmlFile == File() || ! _xmlFile.exists())
    {
        // <SCALA_DATA>
        XmlElement scala_data ("SCALA_DATA");
        
        //   <COLUMNS>
        XmlElement* columns = new XmlElement ("COLUMNS");
        scala_data.addChildElement(columns);
        auto add_column = [&] (int columnId, String name, int width, int visible, int editable, int sortable)
        {
            XmlElement* column = new XmlElement ("COLUMN");
            column->setAttribute ("columnId", columnId);
            column->setAttribute ("name", name);
            column->setAttribute ("width", width);
            column->setAttribute ("visible", visible);
            column->setAttribute ("editable", editable);
            column->setAttribute ("sortable", sortable);
            columns->addChildElement(column);
        };
        
        // if you change any of these properties you must recreate xml
        auto const iw = FavoritesIconRenderer::icon_dimension;
        add_column(1, "ID"             ,  25, 1, 0, 1); // ID: unique, increasing number
        add_column(2, "Icon"           ,  iw, 1, 0, 0); // icon url, or name
        add_column(3, "scl"           , 160, 1, 0, 1); // name of .scl
        add_column(4, "kbm"           , 160, 0, 0, 1); // name of .kbm file
        add_column(5, "Period"         ,  40, 1, 0, 1); // period, octave
        add_column(6, "NPO"            ,  30, 1, 0, 1); // notes per octave, notes per period
        add_column(7, "Description"    , 250, 0, 0, 0); // user description
        add_column(8, "Scala"          , 250, 1, 0, 1); // contents of .scl file as utf8 string
        add_column(9, "Keyboard_Map"   , 250, 0, 0, 0); // contents of .kbm file as utf8 string
        
        //   <DATA>
        XmlElement* data = new XmlElement ("DATA");
        scala_data.addChildElement(data);
        
        // assign and save
        _scalaLibrary = make_unique<XmlElement> (std::move(scala_data));
        jassert(_scalaLibrary != nullptr);
        _writeScalaLibraryToDisk();
    }
    else
    {
        // just read and validate
        _scalaLibrary = XmlDocument::parse(_xmlFile);
    }
    
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
        Columns c(columnXml->getStringAttribute ("name"),
                  columnXml->getIntAttribute ("columnId"),
                  columnXml->getIntAttribute ("width"),
                  50, // unused actually
                  400, // unused actually
                  visibleFlag, // overwritten later if visible == 0
                  -1, // insertIndex, unused
                  columnXml->getIntAttribute ("visible"),
                  columnXml->getIntAttribute ("editable"),
                  columnXml->getIntAttribute ("sortable")
                  );
        _columns.push_back(c);
    }
    
    // _columns is never mutated after this
    
    // debug
    //_logXML();
}

#pragma mark - public methods

// nop if ID does not exist
shared_ptr<ScalaTuningImp> ScalaUserModel::getScalaTuningForID(int ID)
{
    jassert(ID >= ScalaModel::getScalaUserMinID());
    jassert(ID <= ScalaModel::getScalaUserMaxID());
    
    shared_ptr<ScalaTuningImp> retVal = nullptr;
    auto const row = _getRowForID(ID);
    if(row != -1)
    {
        retVal = getScalaTuningForRow(row);
    }
    else
    {
        DBG("ScalaUserModel::getScalaTuningForID: failed to get tuning for ID:" + String(ID));
        ScalaComponentMessageBus::getInstance().broadcastMessage("Failed to get User Scala file for ID: " + String(ID));
    }
    
    return retVal;
}

// Return ScalaTuningImp of Scala file at row_number.
// Lazily creates icon for both bundled and user.
shared_ptr<ScalaTuningImp> ScalaUserModel::getScalaTuningForRow(int row_number)
{
    // lock
    const ScopedLock sl(_lock);
    
    // load .scl and optional .kbm
    auto kbm_file_name = getText(row_number, 4);
    if(kbm_file_name.isNotEmpty())
    {
        auto kbm_file = _fullPathToSclFile(kbm_file_name);
        // TODO: we need to parse kbm file and adjust tuning below
        DBG("ScalaUserModel::getScalaTuningForRow: row: " + String(row_number) + ", reminder we need to parse kbm file, which is being ignored for now");
    }
    
    //
    auto scl_file_name = _getIconFilename(row_number); // icon file name same as .scl
    auto scl_file = _fullPathToSclFile(scl_file_name);
    if(!scl_file.existsAsFile())
    {
        auto debug = "ScalaUserModel::getScalaTuningForRow: row: " + String(row_number) + ", file_name:" + scl_file_name + ": FATAL...file doesn't exist";
        DBG(debug);
        ScalaComponentMessageBus::getInstance().broadcastMessage("Can not load User Scala file: " + scl_file_name + " at row number: " + String(row_number));
        
        return nullptr;
    }
    
    // parse the scala file and create the Tuning
    auto scala_tuning = ScalaTuningImp::createScalaTuningFromSclKbm(scl_file.getFullPathName(), scl_file.getFullPathName()); // TODO: KBM
    if(scala_tuning == nullptr)
    {
        auto debug = "ScalaUserModel::getScalaTuningForRow: row: " + String(row_number) + ", file_name:" + scl_file_name + ": FATAL...can't parse file";
        DBG(debug);
        ScalaComponentMessageBus::getInstance().broadcastMessage("Can not parse User Scala file: " + scl_file_name + ", at row: " + String(row_number));
        
        return nullptr;
    }
    
    // this code duplicated in ScalaBundleModel
    
    // create icon if necessary
    auto icon_file = _fullPathToIconFile(scl_file_name);
    auto image = ImageFileFormat::loadFrom(icon_file);
    if(!image.isValid())
    {
        // create bounds for icon
        auto dim = ScalaIconRenderer::icon_dimension_render;
        auto const bounds = Rectangle<int> (0, 0, dim, dim);
        
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
            DBG("ScalaUserModel::getScalaTuningForRow: " + String(row_number) + "Error writing icon: " + icon_file.getFullPathName());
            ScalaComponentMessageBus::getInstance().broadcastMessage("Internal Error: Can not create icon: " + icon_file.getFullPathName());
        }
    }
    
    // selection state
    auto const ID = getIDForRow(row_number);
    if(ID >= ScalaModel::getScalaUserMinID() && ID <= ScalaModel::getScalaUserMaxID())
    {
        _selectedID = ID;
        selectRow(row_number);
    }
    else
    {
        DBG ("ScalaUserModel::getScalaTuningForRow: ID for row failed!");
        ScalaComponentMessageBus::getInstance().broadcastMessage("Internal Error: Can not get ID for row: " + String(row_number));
    }
    
    return scala_tuning;
}

// this code duplicated in ScalaBundleModel
shared_ptr<ScalaTuningImp> ScalaUserModel::recallPreviousScala()
{
    // lock
    const ScopedLock sl(_lock);
    
    // valid selectedID and row?
    auto const num_rows = getNumRows();
    auto row = _getRowForID(_selectedID);
    if(row < 0 || getNumRows() < 1)
    {
        DBG ("ScalaUserModel::recallPreviousScala: _getRowForID _selectedID = -1");
        ScalaComponentMessageBus::getInstance().broadcastMessage("Can not recall previous User Scala");
        
        return nullptr;
    }
    
    if(num_rows > 1)
    {
        row = (row - 1 + num_rows) % num_rows; // Corrected calculation ChatGPT4
    }
    else if(num_rows == 1)
    {
        row = 0;
    }
    else
    {
        // no user scala files yet
        DBG ("ScalaUserModel::recallPreviousScala: no user scala files yet");
        ScalaComponentMessageBus::getInstance().broadcastMessage("No User Scala files created yet");
        
        return nullptr;
    }
    
    return getScalaTuningForRow(row); // sets _selectedID
}

// this code duplicated in ScalaBundleModel
shared_ptr<ScalaTuningImp> ScalaUserModel::recallNextScala()
{
    // lock
    const ScopedLock sl(_lock);
    
    // valid selectedID and row?
    auto const num_rows = getNumRows();
    auto row = _getRowForID(_selectedID);
    if(row < 0 || getNumRows() < 1)
    {
        DBG ("ScalaUserModel::recallPreviousScala: _getRowForID _selectedID = -1");
        ScalaComponentMessageBus::getInstance().broadcastMessage("Can not recall next User Scala file");
        
        return nullptr;
    }
    
    if(num_rows > 1)
    {
        row = (row + 1) % num_rows; // Corrected calculation ChatGPT4
    }
    else if(num_rows == 1)
    {
        row = 0;
    }
    else
    {
        // no user scala files yet
        DBG ("ScalaUserModel::recallNextScala: no user scala files yet");
        ScalaComponentMessageBus::getInstance().broadcastMessage("No User Scala files created yet");
        
        return nullptr;
    }
    
    return getScalaTuningForRow(row); // sets _selectedID
}

bool ScalaUserModel::deleteScalaTuningAtRow(int row_number)
{
    // lock
    const ScopedLock sl(_lock);
    
    // identify the element from the database
    auto const child = _dataList->getChildElement(row_number);
    if(child == nullptr)
    {
        // FATAL: this should not happen because we accessed this row above
        DBG ("FATAL: ScalaUserModel::deleteScalaTuningAtRow: row_number not found:" + String(row_number));
        
        jassertfalse;
        return false;
    }
    
    // delete .scl, .kbm, and icon
    auto scl_file_name = getText(row_number, 3);
    
    // .scl
    auto full_path_to_scl_file = _fullPathToSclFile(scl_file_name);
    auto scl_file = File(full_path_to_scl_file);
    scl_file.moveToTrash();
    
    // .kbm
    auto kbm_file_name = getText(row_number, 4);
    if(kbm_file_name.length() > 0)
    {
        auto full_path_to_kbm_file = _fullPathToSclFile(kbm_file_name);
        auto kbm_file = File(full_path_to_kbm_file);
        if(kbm_file.existsAsFile())
        {
            kbm_file.moveToTrash();
        }
    }
    
    // delete icon, if it exists
    auto full_path_to_icon_file = _fullPathToIconFile(scl_file_name);
    auto icon_file = File(full_path_to_icon_file);
    if(icon_file.existsAsFile())
    {
        icon_file.moveToTrash();
    }
    
    // delete the element
    _dataList->removeChildElement(child, true);
    
    // Write file
    _writeScalaLibraryToDisk();
    
    // _selectedID is now invalid
    _selectedID = -1; // bad design
    
    //
    return true;
}

// this code duplicated in ScalaBundleModel
int ScalaUserModel::getSelectedRowNumber()
{
    auto const retVal = _getRowForID(_selectedID);
    
    return retVal;
}

int ScalaUserModel::getSelectedID()
{
    return _selectedID;
}

unordered_map<int, int> ScalaUserModel::getIntegrityCheck()
{
    // lock
    const ScopedLock sl(_lock);
        
    // assert on duplicates
    unordered_map<int, int> integrity {};
    for(auto data : _dataList->getChildIterator())
    {
        auto const ID = data->getIntAttribute("ID");
        auto it = integrity.find(ID);
        if(it == integrity.end() && (ID >= ScalaModel::getScalaUserMinID()) && (ID <= ScalaModel::getScalaUserMaxID()))
        {
            DBG("user Scala ID: " + String(ID));
            integrity[ID] = ID;
        }
        else
        {
            // we should not have duplicate/invalid IDs
            DBG("Duplicate/Invalid User Scala ID found: " + String(ID));
            jassertfalse;
        }
    }
    
    return integrity;
}

// Given .scl and optional .kbm:
//   creates new SCALA child with attributes ID, Icon, Period, NPO, Description
// Does NOT create icon asset--that happens lazily in getScalaTuningForRow
bool ScalaUserModel::addScalaKbm(File scl_file, File kbm_file)
{
    auto scl_file_name = scl_file.getFileName();
    auto kbm_file_name = kbm_file.getFileName();
    auto scl_full_path = scl_file.getFullPathName();
    auto kbm_full_path = kbm_file.getFullPathName();
    auto scl_file_contents = scl_file.loadFileAsString();
    auto kbm_file_contents = kbm_file.loadFileAsString();
    if(scl_file_contents.isEmpty())
    {
        DBG ("ScalaUserModel::addScalaKbm: cannot add to database because " + scl_file_name + ": is empty");
        ScalaComponentMessageBus::getInstance().broadcastMessage("Can not add User Scala file because " + scl_file_name + " is empty");
        
        return false;
    }
    
    // parse the scala file and create the Tuning
    auto scala_tuning = ScalaTuningImp::createScalaTuningFromSclKbm(scl_full_path, kbm_full_path);
    if(scala_tuning == nullptr)
    {
        auto debug = "ScalaUserModel::addScalaKbm: cannot create tuning because " + scl_file_name + ": is invalid";
        DBG(debug);
        ScalaComponentMessageBus::getInstance().broadcastMessage("Can not create User Scala file because " + scl_file_name + " is invalid");
        
        return false;
    }
    
    // new Scala file entry
    auto new_scala = new XmlElement ("SCALA");
    
    // create new id
    auto const id = _getNewID();
    if(id == -1)
    {
        ScalaComponentMessageBus::getInstance().broadcastMessage("Internal Error: Can't add Scala file because a new ID cannot be created");
        
        return false;
    }
    
    //
    new_scala->setAttribute ("ID", id);
    
    // TODO: we actually don't need to store data for the icon column
    auto const icon_url = "dont need data for this column";
    new_scala->setAttribute ("Icon", icon_url);
    
    // .scl filename
    new_scala->setAttribute ("scl", scl_file_name);
    
    // .kbm filename
    new_scala->setAttribute ("kbm", kbm_file_name);
    
    // Period
    new_scala->setAttribute ("Period", scala_tuning->getRepeatingInterval());
    
    // NPO
    new_scala->setAttribute("NPO", static_cast<int>(scala_tuning->getProcessedArrayCount()));
    
    // Description (! comments)
    auto desc = scala_tuning->getTuningDescription();
    new_scala->setAttribute ("Description", desc);
    
    // contents of scala file as utf8 string
    new_scala->setAttribute ("Scala", scl_file_contents);
    
    // contents of kbm file(if any) as utf8 string
    new_scala->setAttribute ("Keyboard_Map", kbm_file_contents);
    
    // Add to database
    
    // lock
    const ScopedLock sl(_lock);
    _dataList->addChildElement(new_scala);
    
    // write file
    _writeScalaLibraryToDisk();
    
    //
    return true;
}

// TODO: left off here
// The kbm is created no matter what by TuningImp...the question is if you want to add it to db
bool ScalaUserModel::addScalaFromTuning(shared_ptr<Tuning> tuning, bool /* create_kbm */)
{
    auto sf = tuning->tuningAsScala();
    auto name = tuning->defaultScalaName();
    
    return false;
}

#pragma mark - TableListBoxModel

// this code duplicated in ScalaBundleModel
int ScalaUserModel::getNumRows()
{
    // lock
    const ScopedLock sl(_lock);
    
    return _scalaLibrary->getChildByName("DATA")->getNumChildElements();
}

// this code duplicated in ScalaBundleModel
int ScalaUserModel::getColumnAutoSizeWidth(int columnId)
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

// this code duplicated in ScalaBundleModel
void ScalaUserModel::sortOrderChanged(int new_sort_column_id, bool is_forwards)
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

Font ScalaUserModel::getFont()
{
    return _font;
}

// this code duplicated in ScalaBundleModel
String ScalaUserModel::getText(int rowNumber, int columnId)
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

void ScalaUserModel::setText(String columnName, const int rowNumber, const String& newText)
{
    // lock
    const ScopedLock sl(_lock);
    
    // set text
    _dataList->getChildElement(rowNumber)->setAttribute(columnName, newText);
    
    // store on disk
    _writeScalaLibraryToDisk();
}

// this code duplicated in ScalaBundleModel
int ScalaUserModel::getIsSelectedForRow(const int rowNumber) const
{
    // lock
    const ScopedLock sl(_lock);
    
    // get selection
    return _dataList->getChildElement(rowNumber)->getIntAttribute ("Select");
}

// this code duplicated in ScalaBundleModel
void ScalaUserModel::selectRow(const int rowNumber)
{
    // lock
    const ScopedLock sl(_lock);
    
    // deselect all
    for(auto data : _dataList->getChildIterator())
    {
        data->setAttribute ("Select", 0);
    }
    
    // select
    _dataList->getChildElement(rowNumber)->setAttribute ("Select", 1);
}

// this code duplicated in ScalaBundleModel
vector<Columns> ScalaUserModel::getColumns()
{
    return _columns;
}

// this code duplicated in ScalaBundleModel
shared_ptr<Image> ScalaUserModel::getIcon(int row_number)
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

// Creates a File from the constructed full path.
// Doesn't mean it's a valid file
File ScalaUserModel::_fullPathToSclFile(String file_name)
{
    auto full_path = File(_scalaFileDirectory.getFullPathName() + "/" + file_name);
    
    return full_path;
}

// this code duplicated in ScalaBundleModel
// icons are lazily created so they may not exist.
File ScalaUserModel::_fullPathToIconFile(String file_name)
{
    auto full_path = File(_iconCacheDirectory.getFullPathName() + "/" + file_name);
    
    return full_path;
}

// this code duplicated in ScalaBundleModel
String ScalaUserModel::_getIconFilename(int rowNumber)
{
    return getText(rowNumber, 3);  // id 3 is scala filename
}

bool ScalaUserModel::_writeScalaLibraryToDisk()
{
    // lock
    const ScopedLock sl(_lock);
    
    // must be a valid favorites library
    jassert(_scalaLibrary != nullptr);
    auto fl = _scalaLibrary->toString();
    
    // TODO: replace this with writeTo
    auto success = _xmlFile.replaceWithText(fl);
    jassert(success == true); // for now this is fatal
    
    // debug
    //_logXML();
    
    return success;
}

// this code duplicated in ScalaBundleModel
void ScalaUserModel::_logXML()
{
    // lock
    const ScopedLock sl(_lock);
    
    // default
    auto root_as_xml = _scalaLibrary->toString();
    DBG("ScalaUserModel::_logXML: scala user library as xml string:");
    DBG(root_as_xml);
    DBG("");
}

// this code duplicated in ScalaBundleModel
String ScalaUserModel::_getAttributeNameForColumnId(const int columnId) const
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

// return the first available id
int ScalaUserModel::_getNewID()
{
    // lock
    const ScopedLock sl(_lock);
    
    // Collect all IDs into a vector
    vector<int> ids;
    for(auto data : _dataList->getChildIterator())
    {
        ids.push_back(data->getIntAttribute("ID"));
    }
    
    // Sort the vector of IDs
    sort(ids.begin(), ids.end());
    
    // Find the first available ID
    int newID = ScalaModel::getScalaUserMinID(); // 1
    for(int id : ids)
    {
        if(id == newID)
        {
            newID++;
        }
        else if(id > newID)
        {
            break; // Found a gap
        }
    }
    
    if(newID > ScalaModel::getScalaUserMaxID())
    {
        return -1; // Or handle the error as appropriate
    }
    
    return newID;
}

// this code duplicated in ScalaBundleModel
int ScalaUserModel::getIDForRow(int row_number)
{
    // lock
    const ScopedLock sl(_lock);
    
    int row = 0;
    for(auto data : _dataList->getChildIterator())
    {
        if(row == row_number)
        {
            auto id_number = data->getIntAttribute ("ID");
            return id_number;
        }
        row++;
    }
    
    // if you get here it's because you asked for a row number that's out of range
    return -1;
}

// this code duplicated in ScalaBundleModel
int ScalaUserModel::_getRowForID(int id_number)
{
    // lock
    const ScopedLock sl(_lock);
    
    if(id_number >= ScalaModel::getScalaUserMinID() && id_number <= ScalaModel::getScalaUserMaxID())
    {
        
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
    }
    
    // if you get here it's because you asked for an id that doesn't/shouldn't exist in _dataList
    return -1;
}
