# Orthy Application

## Overview
Orthy is a versatile application designed for image manipulation and management, featuring a plugin system that allows for extensibility and customization. The application provides a user-friendly interface for loading, displaying, and transforming images, making it suitable for various use cases.

## Features
- **Plugin System**: Easily extend the functionality of the application by adding custom plugins.
- **Image Manipulation**: Load, rotate, scale, and adjust the transparency of images.
- **User Interface**: Intuitive controls for managing images and plugins.

## Installation
1. Clone the repository:
   ```
   git clone https://github.com/yourusername/Orthy_beta.git
   ```
2. Navigate to the project directory:
   ```
   cd Orthy_beta
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
To run the application, execute the following command:
```
python orthy.py
```

## Directory Structure
```
Orthy_beta
├── core
│   ├── OrthyPlugin_Interface.py
│   └── plugin_loader.py
├── Images
│   └── ArchSaves
├── orthy.py
├── requirements.txt
└── README.md
```

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.