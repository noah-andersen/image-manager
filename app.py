import streamlit as st
import json
import csv
import os
from pathlib import Path
import shutil
from PIL import Image
import uuid

# Page configuration
st.set_page_config(
    page_title="Card Image Dataset Manager",
    page_icon="🃏",
    layout="wide"
)

# Initialize session state
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'dataset' not in st.session_state:
    st.session_state.dataset = []
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'base_path' not in st.session_state:
    st.session_state.base_path = None
if 'modified_items' not in st.session_state:
    st.session_state.modified_items = set()
if 'deleted_items' not in st.session_state:
    st.session_state.deleted_items = set()

def load_dataset(file_path, base_path):
    """Load dataset from JSON or CSV file"""
    file_path = Path(file_path)
    
    # Determine file type and load accordingly
    if file_path.suffix.lower() == '.json':
        # Load JSON format
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Handle both list and single object
        if isinstance(data, dict):
            data = [data]
    
    elif file_path.suffix.lower() == '.csv':
        # Load CSV format
        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert CSV row to expected format
                item = {
                    'title': row.get('title', ''),
                    'card_name': row.get('card_name', ''),
                    'grading_company': row.get('grading_company', ''),
                    'grade': row.get('grade', ''),
                    'price': row.get('price', ''),
                    'listing_url': row.get('listing_url', ''),
                    'listing_id': row.get('listing_id', ''),
                    'source': row.get('source', ''),
                    'scraped_date': row.get('scraped_date', ''),
                }
                
                # Parse comma-separated image_urls
                if 'image_urls' in row and row['image_urls']:
                    item['image_urls'] = [url.strip() for url in row['image_urls'].split(',')]
                else:
                    item['image_urls'] = []
                
                # Parse comma-separated images (local paths)
                if 'images' in row and row['images']:
                    item['images'] = [img.strip() for img in row['images'].split(',')]
                else:
                    item['images'] = []
                
                data.append(item)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}. Use .json or .csv")
    
    st.session_state.dataset = data
    st.session_state.base_path = base_path
    st.session_state.data_loaded = True
    st.session_state.current_index = 0
    st.session_state.modified_items = set()
    st.session_state.deleted_items = set()

def get_full_image_path(image_rel_path):
    """Convert relative image path to full path"""
    return os.path.join(st.session_state.base_path, image_rel_path)

def delete_image(item_index, image_index):
    """Delete an image from the dataset"""
    item = st.session_state.dataset[item_index]
    if image_index < len(item['images']):
        image_path = get_full_image_path(item['images'][image_index])
        if os.path.exists(image_path):
            os.remove(image_path)
        item['images'].pop(image_index)
        st.session_state.modified_items.add(item_index)

def delete_listing(item_index):
    """Mark listing for deletion (won't be exported)"""
    # Mark the item as deleted
    st.session_state.deleted_items.add(item_index)
    
    # Remove from modified items if present
    if item_index in st.session_state.modified_items:
        st.session_state.modified_items.remove(item_index)
    
    # Move to next item
    if st.session_state.current_index < len(st.session_state.dataset) - 1:
        st.session_state.current_index += 1

def swap_images(item_index, index1, index2):
    """Swap two images in the dataset"""
    item = st.session_state.dataset[item_index]
    if index1 < len(item['images']) and index2 < len(item['images']):
        item['images'][index1], item['images'][index2] = item['images'][index2], item['images'][index1]
        st.session_state.modified_items.add(item_index)

def update_metadata(item_index, grade, grading_company):
    """Update grade and grading company for an item"""
    st.session_state.dataset[item_index]['grade'] = grade
    st.session_state.dataset[item_index]['grading_company'] = grading_company
    st.session_state.modified_items.add(item_index)
    
    # Move to next item
    if st.session_state.current_index < len(st.session_state.dataset) - 1:
        st.session_state.current_index += 1

def undelete_listing(item_index):
    """Unmark listing for deletion"""
    if item_index in st.session_state.deleted_items:
        st.session_state.deleted_items.remove(item_index)

def export_dataset(output_dir):
    """Export organized dataset"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    exported_count = 0
    skipped_count = 0
    export_log = []
    
    for idx, item in enumerate(st.session_state.dataset):
        # Skip items marked for deletion
        if idx in st.session_state.deleted_items:
            skipped_count += 1
            export_log.append(f"Skipped: {item.get('listing_id', 'unknown')} - Marked for deletion")
            continue
        
        # Skip items without grade or grading company
        if not item.get('grade') or not item.get('grading_company'):
            skipped_count += 1
            export_log.append(f"Skipped: {item.get('listing_id', 'unknown')} - Missing grade or grading company")
            continue
        
        # Skip items without exactly 2 images (front and back)
        if len(item.get('images', [])) != 2:
            skipped_count += 1
            export_log.append(f"Skipped: {item.get('listing_id', 'unknown')} - Need exactly 2 images (front/back)")
            continue
        
        # Create directory structure: output_dir/grading_company/
        company_dir = output_path / item['grading_company']
        company_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique ID
        unique_id = str(uuid.uuid4())[:8]
        
        # Copy and rename images
        try:
            for idx, image_rel_path in enumerate(item['images']):
                source_path = get_full_image_path(image_rel_path)
                if not os.path.exists(source_path):
                    raise FileNotFoundError(f"Image not found: {source_path}")
                
                # Determine file extension
                ext = Path(source_path).suffix
                
                # Name: grade_uniqueid_front.ext or grade_uniqueid_back.ext
                image_type = "front" if idx == 0 else "back"
                new_filename = f"{item['grade']}_{unique_id}_{image_type}{ext}"
                dest_path = company_dir / new_filename
                
                shutil.copy2(source_path, dest_path)
            
            exported_count += 1
            export_log.append(f"Exported: {item.get('listing_id', 'unknown')} as {unique_id}")
        
        except Exception as e:
            skipped_count += 1
            export_log.append(f"Error exporting {item.get('listing_id', 'unknown')}: {str(e)}")
    
    # Save updated dataset JSON
    output_json = output_path / "dataset_metadata.json"
    with open(output_json, 'w') as f:
        json.dump(st.session_state.dataset, f, indent=2)
    
    return exported_count, skipped_count, export_log

# Sidebar for configuration
st.sidebar.title("🃏 Dataset Manager")

# Load dataset section
st.sidebar.header("1. Load Dataset")
data_file = st.sidebar.text_input("Data File Path (JSON or CSV)", placeholder="/path/to/data.json or /path/to/data.csv")
base_path = st.sidebar.text_input("Base Images Path", placeholder="/path/to/images/")

if st.sidebar.button("Load Dataset"):
    if os.path.exists(data_file) and os.path.exists(base_path):
        try:
            load_dataset(data_file, base_path)
            st.sidebar.success(f"Loaded {len(st.session_state.dataset)} items")
        except Exception as e:
            st.sidebar.error(f"Error loading dataset: {str(e)}")
    else:
        st.sidebar.error("Invalid file paths")

# Navigation
if st.session_state.data_loaded:
    st.sidebar.header("2. Navigation")
    total_items = len(st.session_state.dataset)
    
    col1, col2, col3 = st.sidebar.columns(3)
    with col1:
        if st.button("⬅️ Prev"):
            if st.session_state.current_index > 0:
                st.session_state.current_index -= 1
    with col2:
        st.write(f"{st.session_state.current_index + 1}/{total_items}")
    with col3:
        if st.button("Next ➡️"):
            if st.session_state.current_index < total_items - 1:
                st.session_state.current_index += 1
    
    # Jump to specific item
    jump_to = st.sidebar.number_input("Jump to item:", min_value=1, max_value=total_items, value=st.session_state.current_index + 1)
    if st.sidebar.button("Go"):
        st.session_state.current_index = jump_to - 1
    
    # Export section
    st.sidebar.header("3. Export Dataset")
    output_dir = st.sidebar.text_input("Output Directory", placeholder="/path/to/output/")
    
    if st.sidebar.button("Export Organized Dataset"):
        if output_dir:
            with st.spinner("Exporting dataset..."):
                exported, skipped, log = export_dataset(output_dir)
            st.sidebar.success(f"Exported: {exported} | Skipped: {skipped}")
            with st.sidebar.expander("Export Log"):
                for entry in log:
                    st.text(entry)
        else:
            st.sidebar.error("Please specify output directory")
    
    # Stats
    st.sidebar.header("Stats")
    st.sidebar.metric("Total Items", total_items)
    st.sidebar.metric("Marked for Deletion", len(st.session_state.deleted_items))
    st.sidebar.metric("Modified", len(st.session_state.modified_items))
    
    # Count items with valid data (excluding deleted)
    valid_count = sum(1 for idx, item in enumerate(st.session_state.dataset)
                     if idx not in st.session_state.deleted_items
                     and item.get('grade') 
                     and item.get('grading_company') 
                     and len(item.get('images', [])) == 2)
    st.sidebar.metric("Ready to Export", valid_count)
    
    # Info section
    st.sidebar.header("Info")
    st.sidebar.info("ℹ️ For export, you need exactly 2 images (front and back). First image = Front, Second image = Back")

# Main content area
if st.session_state.data_loaded:
    current_item = st.session_state.dataset[st.session_state.current_index]
    is_deleted = st.session_state.current_index in st.session_state.deleted_items
    
    st.title(f"Card Dataset Manager - Item {st.session_state.current_index + 1}")
    
    # Show deletion status
    if is_deleted:
        st.error("⚠️ This listing is marked for deletion and will not be exported")
    
    st.markdown("---")
    
    # Consolidated title and info
    st.subheader(current_item.get('title', 'N/A'))
    
    # Compact info display
    info_col1, info_col2, info_col3, info_col4 = st.columns(4)
    with info_col1:
        st.metric("Price", f"${current_item.get('price', 0)}")
    with info_col2:
        st.metric("Listing ID", current_item.get('listing_id', 'N/A'))
    with info_col3:
        st.metric("Images", len(current_item.get('images', [])))
    with info_col4:
        if current_item.get('listing_url'):
            st.markdown(f"[View Listing]({current_item['listing_url']})")
    
    # Check for missing data
    has_missing_data = not current_item.get('grade') or not current_item.get('grading_company')
    
    if has_missing_data:
        st.error("⚠️ MISSING DATA: This item is missing grade and/or grading company information!")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        grading_companies = ['PSA', 'CGC', 'BGS', 'SGC', 'Other']
        current_company = current_item.get('grading_company', '')
        
        # Add current company to list if not in default list
        if current_company and current_company not in grading_companies:
            grading_companies.insert(0, current_company)
        
        # Add empty option at the beginning
        if '' not in grading_companies:
            grading_companies.insert(0, '')
        
        # Determine index
        try:
            company_index = grading_companies.index(current_company) if current_company else 0
        except ValueError:
            company_index = 0
        
        # Red label if missing
        company_label = "Grading Company" if current_company else "⚠️ Grading Company (MISSING)"
        
        new_company = st.selectbox(
            company_label,
            grading_companies,
            index=company_index,
            key=f"company_{st.session_state.current_index}"
        )
    
    with col2:
        # Grade input with red label if missing
        current_grade = current_item.get('grade', '')
        grade_label = "Grade" if current_grade else "⚠️ Grade (MISSING)"
        
        new_grade = st.text_input(
            grade_label,
            value=str(current_grade) if current_grade else '',
            key=f"grade_{st.session_state.current_index}"
        )
    
    with col3:
        st.write("")  # Spacing
        st.write("")  # Spacing
        if st.button("💾 Update", key=f"update_{st.session_state.current_index}"):
            # Convert grade to number if possible
            try:
                grade_value = int(new_grade) if new_grade else None
            except:
                grade_value = new_grade if new_grade else None
            
            update_metadata(st.session_state.current_index, grade_value, new_company)
            st.rerun()
    
    # Action buttons above images
    action_col1, action_col2, action_col3 = st.columns([2, 1, 1])
    with action_col1:
        if not is_deleted:
            st.info("💡 Mark for deletion to skip during export")
    with action_col2:
        if is_deleted:
            if st.button("♻️ Restore Listing", type="primary", use_container_width=True):
                undelete_listing(st.session_state.current_index)
                st.rerun()
        else:
            if st.button("🗑️ Mark for Deletion", type="secondary", use_container_width=True):
                delete_listing(st.session_state.current_index)
                st.rerun()
    with action_col3:
        if st.button("Next ➡️", type="primary", use_container_width=True):
            if st.session_state.current_index < len(st.session_state.dataset) - 1:
                st.session_state.current_index += 1
                st.rerun()
    
    # Image reordering controls
    if len(current_item.get('images', [])) >= 2:
        st.markdown("**Reorder Images:**")
        col_swap1, col_swap2, col_swap3 = st.columns([1, 1, 3])
        with col_swap1:
            if st.button("🔄 Swap 1↔2", help="Swap first and second image"):
                swap_images(st.session_state.current_index, 0, 1)
                st.success("Swapped!")
                st.rerun()
        with col_swap2:
            if len(current_item.get('images', [])) >= 3:
                if st.button("🔄 Swap 2↔3", help="Swap second and third image"):
                    swap_images(st.session_state.current_index, 1, 2)
                    st.success("Swapped!")
                    st.rerun()
    
    images = current_item.get('images', [])
    
    if not images:
        st.warning("No images available for this item")
    else:
        # Display images in columns
        num_images = len(images)
        cols = st.columns(min(num_images, 3))
        
        for idx, image_rel_path in enumerate(images):
            col_idx = idx % 3
            with cols[col_idx]:
                image_path = get_full_image_path(image_rel_path)
                
                if os.path.exists(image_path):
                    try:
                        img = Image.open(image_path)
                        st.image(img, caption=f"Image {idx + 1} - {'Front' if idx == 0 else 'Back' if idx == 1 else 'Extra'}")
                        
                        # Delete button
                        if st.button(f"🗑️ Delete Image {idx + 1}", key=f"delete_{idx}"):
                            delete_image(st.session_state.current_index, idx)
                            st.success(f"Deleted image {idx + 1}")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error loading image: {str(e)}")
                else:
                    st.error(f"Image not found: {image_rel_path}")
        
        # Warning if not exactly 2 images
        if num_images != 2:
            if num_images < 2:
                st.warning(f"⚠️ Need 2 images for export. Currently have {num_images}.")
            else:
                st.warning(f"⚠️ Need exactly 2 images for export. Currently have {num_images}. Please delete extra images.")

else:
    # Welcome screen
    st.title("🃏 Card Image Dataset Manager")
    st.write("""
    ## Welcome!
    
    This application helps you organize and prepare your card image dataset for training.
    
    ### Features:
    - ✅ Browse through your dataset items
    - ✅ View and manage images
    - ✅ Edit metadata (grade, grading company)
    - ✅ Delete unwanted images
    - ✅ Export organized dataset with front/back images
    
    ### Getting Started:
    1. Enter the path to your JSON data file in the sidebar
    2. Enter the base path where your images are stored
    3. Click "Load Dataset" to begin
    
    ### Export Structure:
    ```
    output_directory/
    ├── PSA/
    │   ├── 10_abc123_front.jpg
    │   ├── 10_abc123_back.jpg
    │   ├── 10_def456_front.jpg
    │   ├── 10_def456_back.jpg
    │   ├── 9_xyz789_front.jpg
    │   └── 9_xyz789_back.jpg
    ├── CGC/
    │   ├── 10_aaa111_front.jpg
    │   ├── 10_aaa111_back.jpg
    │   └── 9.5_bbb222_front.jpg
    └── dataset_metadata.json
    ```
    
    ### Requirements:
    - Each card must have exactly 2 images (front and back)
    - Each card must have a valid grade and grading company

    """)
