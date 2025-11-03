# Card Image Dataset Manager

A lightweight Streamlit application for managing and organizing card image datasets for computer vision projects.

## Features

- 📂 **Browse Dataset**: Navigate through your card data with ease
- 🖼️ **Image Management**: View, organize, and delete images
- ✏️ **Edit Metadata**: Correct grades and grading companies
- 🗂️ **Smart Organization**: Export dataset with proper structure for training
- 🔍 **Quality Control**: Ensure each card has exactly 2 images (front/back)

## Installation

1. Clone or navigate to this repository:
```bash
cd /Users/nandersen/git_repos/image-manager
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### 1. Start the Application

```bash
streamlit run app.py
```

### 2. Load Your Dataset

In the sidebar:
- **JSON File Path**: Enter the full path to your JSON file containing the card data
  - Example: `/Users/nandersen/git_repos/ebay-card-scraper/data_scraped/pokemon_psa10.json`
- **Base Images Path**: Enter the base directory where your images are stored
  - Example: `/Users/nandersen/git_repos/ebay-card-scraper/downloaded_images/`
- Click **Load Dataset**

### 3. Review and Organize

For each card:
- Review the title and metadata
- Check all images
- Delete unwanted/duplicate images (keep only front and back)
- Update the grade and grading company if needed
- Navigate using Previous/Next buttons or jump to a specific item

### 4. Export Organized Dataset

When ready:
- Enter the **Output Directory** path in the sidebar
- Click **Export Organized Dataset**
- The app will create a structured dataset:

```
output_directory/
├── PSA/
│   ├── 10_abc12345_front.jpg
│   ├── 10_abc12345_back.jpg
│   ├── 10_def67890_front.jpg
│   ├── 10_def67890_back.jpg
│   ├── 9_ghi11223_front.jpg
│   ├── 9_ghi11223_back.jpg
│   ├── 8_jkl44556_front.jpg
│   └── 8_jkl44556_back.jpg
├── CGC/
│   ├── 10_mno78901_front.jpg
│   ├── 10_mno78901_back.jpg
│   └── 9.5_pqr23456_front.jpg
├── BGS/
│   └── ...
└── dataset_metadata.json
```

## Data Format

Your input JSON should contain card data in this format:

```json
{
  "title": "Card title",
  "card_name": "Card name",
  "grading_company": "PSA",
  "grade": 10,
  "price": 58.45,
  "listing_url": "https://...",
  "listing_id": "123456789",
  "images": [
    "ebay/PSA/123456789_CARD_NAME/image_1.jpg",
    "ebay/PSA/123456789_CARD_NAME/image_2.jpg"
  ]
}
```

Or an array of such objects.

## Export Rules

The application will only export cards that meet these criteria:

1. ✅ Has a valid **grade** value
2. ✅ Has a valid **grading_company** value
3. ✅ Has exactly **2 images** (front and back)

Cards that don't meet these criteria will be skipped (check the export log for details).

## File Naming Convention

Exported images follow this pattern:
```
{grade}_{unique_id}_{type}.{extension}
```

Examples:
- `10_a7b3c9d2_front.jpg`
- `10_a7b3c9d2_back.jpg`
- `9_f4e8d1c6_front.png`
- `9_f4e8d1c6_back.png`

## Tips

- **Image Order Matters**: The first image is considered the front, the second is the back
- **Save Often**: Use the export feature periodically to save your progress
- **Track Progress**: Check the stats in the sidebar to see how many cards are ready to export
- **Batch Process**: You can load, organize, and export multiple times with different filters

## Workflow Example

1. Load your scraped eBay data
2. Navigate through items checking image quality
3. Delete blurry or duplicate images
4. Correct any mislabeled grades or grading companies
5. Ensure each card has exactly 2 images (front/back)
6. Export the organized dataset
7. Use the organized dataset to train your computer vision model

## Troubleshooting

### "Image not found" error
- Verify that the base path is correct
- Check that image paths in your JSON are relative to the base path

### Export skips all items
- Ensure cards have valid grade and grading_company values
- Make sure each card has exactly 2 images

### Images don't display
- Check file permissions
- Verify image file extensions are supported (.jpg, .png, .jpeg)

## Project Structure

```
image-manager/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── .gitignore         # Git ignore patterns
```

## Future Enhancements

Potential features to add:
- [ ] Batch editing capabilities
- [ ] Image rotation/cropping tools
- [ ] Automatic duplicate detection
- [ ] Integration with labeling tools
- [ ] Preview dataset statistics (grade distribution, etc.)
- [ ] Support for more than 2 images per card
- [ ] Undo/redo functionality

## License

MIT License - See LICENSE file for details
