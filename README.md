# Wilsonic MTS-ESP

<img src="./Resources/wilsonic_icon_03_512.png" alt="Wilsonic Icon" width="200">

Wilsonic MTS-ESP is an advanced audio plugin and standalone application for creative sound design and music production. It tunes up the software synthesizers in your DAW via MTS-ESP to the scale designs of Erv Wilson; it has a simple synth that you can use to confirm your synths are all in tune.  The Wilsonic Controller target outputs MIDI, while also tuning up all soft synths in your DAW via MTS-ESP.  You can use WilsonicController to perform on Wilson's generalized keyboard designs.

## Features

- Interactive musical scale design and visualization of the tuning systems of Erv Wilson
- Scale design parameters are automatable in your DAW, and therefore editable
- Standalone application and plugin formats (VST3, AU)
- MTS-ESP support for microtuning
- WilsonicController outputs MIDI, while also tuning up all soft synths in your DAW via MTS-ESP
- Cross-platform compatibility (macOS, Windows)

## Installation

### macOS

1. Download the latest Wilsonic installer for macOS from the [releases page](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/releases).
2. Open the downloaded `.zip` file and follow the installation wizard.
3. The standalone application will be installed in your Applications folder.
4. Audio Unit (AU) and VST3 plugins will be installed in their respective system folders.

### Windows

1. Download the latest Wilsonic installer for Windows 10 from the [releases page](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/releases).
2. Run the downloaded `.exe` file and follow the installation wizard.
3. The standalone application will be installed in the specified location (default: Program Files).
4. VST3 plugins will be installed in the system VST3 folder.

## Building from Source

### Prerequisites

- Projucer (part of the JUCE framework)
- C++17 compatible compiler
- Xcode (for macOS) or Visual Studio (for Windows)

### Build Instructions

1. Clone the repository:
   ```
   git clone https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP.git
   cd Wilsonic-MTS-ESP
   ```

2. Open the Wilsonic.jucer or WilsonicController.jucer file in Projucer.

3. In Projucer, select your target IDE (Xcode for macOS or Visual Studio for Windows) and click "Save and Open in IDE".

4. Build the project in your IDE:
   - For Xcode: Select the desired target and click "Build"
   - For Visual Studio: Select the desired configuration and platform, then build the solution

5. The built standalone application and plugins will be in the "Builds" directory.

For more detailed build commands and platform-specific instructions, see [CLAUDE.md](./CLAUDE.md#build-commands).

## Running Tests

Compile and execute the unit tests with:

```bash
make -C tests
./tests/test_wilsonicmath
```

## Usage

Refer to the [User Manual](https://drive.google.com/file/d/1BrTWlS9N4a0xTRUzwLxwr5R5JJ2RvF8n) for detailed instructions on how to use Wilsonic.

## Design Philosophy

Wilsonic MTS-ESP is designed to enable professional music production with microtonal scale designs by Erv Wilson in the DAW of your choice, where all the parameters to the scale design are automatable in the DAW.  See [parameters](./daw_automated_params.txt) for a list of the parameters that can be automated.

The source of truth for all state is therefore JUCE's AudioProcessorValueTreeState.  The Processor owns the APVTS and all Models.  The Model objects own the Tuning objects, and bind them to APVTS, and provide an interface for the UI objects.  The Tuning objects are responsible for generating the MTS-ESP data.  Tuning objects know how to draw themselves.  Components delegate drawing to the Model objects, which pass the drawing on to the Tuning objects.  

The Editor is only responsible for rendering the UI, which is implemented as a LookAndFeel and Component hierarchy.  The Editor is not guaranteed to ever be created.

For a detailed technical overview of the architecture and development guidelines, see [CLAUDE.md](./CLAUDE.md#architecture-overview). 

## Contributing

We welcome contributions to Wilsonic! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and suggest improvements.

For developers: See [CLAUDE.md](./CLAUDE.md) for detailed technical documentation about the codebase architecture, build system, and especially important guidance on adding new scale designs.

## License

Wilsonic is released under the [MIT License](LICENSE).

## Acknowledgements

- [JUCE](https://juce.com/) - Cross-platform audio application framework
- [MTS-ESP](https://github.com/ODDSound/MTS-ESP) - Microtuning support library

## Contact

For support or inquiries, please [open an issue](https://github.com/marcus-w-hobbs/Wilsonic-MTS-ESP/issues) on this repository.
