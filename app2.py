import streamlit as st
import os
from pathlib import Path
from PIL import Image
import re

# Page configuration
st.set_page_config(
    page_title="Card Grade Classifier",
    page_icon="🎴",
    layout="wide"
)

# Initialize session state
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'card_pairs' not in st.session_state:
    st.session_state.card_pairs = []
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'source_dir' not in st.session_state:
    st.session_state.source_dir = None
if 'classified_count' not in st.session_state:
    st.session_state.classified_count = 0

def parse_filename(filename):
    """Parse filename to extract grade, unique_id, and side (front/back)"""
    pattern = r'^([\d.]+)_([a-f0-9]+)_(front|back)\.(\w+)$'
    match = re.match(pattern, filename, re.IGNORECASE)
    if match:
        grade = match.group(1)
        unique_id = match.group(2)
        side = match.group(3).lower()
        extension = match.group(4)
        return grade, unique_id, side, extension
    return None, None, None, None

def is_grade_10(grade_str):
    """Check if grade is 10 or 10.0"""
    try:
        grade_float = float(grade_str)
        return grade_float == 10.0
    except:
        return False

def load_image_directory(directory_path):
    """Load and pair images from directory, filtering for grade 10/10.0"""
    directory = Path(directory_path)
    
    if not directory.exists():
        st.error(f"Directory does not exist: {directory_path}")
        return
    
    # Dictionary to group images by unique_id
    image_dict = {}
    
    # Scan all files in directory
    for file in directory.iterdir():
        if file.is_file() and file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
            grade, unique_id, side, extension = parse_filename(file.name)
            
            if grade and unique_id and side and is_grade_10(grade):
                if unique_id not in image_dict:
                    image_dict[unique_id] = {
                        'grade': grade,
                        'unique_id': unique_id,
                        'extension': extension,
                        'front': None,
                        'back': None
                    }
                
                image_dict[unique_id][side] = file.name
    
    # Filter to only pairs that have both front and back
    card_pairs = []
    for unique_id, data in image_dict.items():
        if data['front'] and data['back']:
            card_pairs.append(data)
    
    # Sort by unique_id for consistency
    card_pairs.sort(key=lambda x: x['unique_id'])
    
    st.session_state.card_pairs = card_pairs
    st.session_state.source_dir = directory_path
    st.session_state.data_loaded = True
    st.session_state.current_index = 0
    st.session_state.classified_count = 0

def rename_card_pair(card_pair, new_grade):
    """Rename both front and back images with new grade"""
    source_dir = Path(st.session_state.source_dir)
    
    old_front = source_dir / card_pair['front']
    old_back = source_dir / card_pair['back']
    
    # Create new filenames with new grade
    new_front_name = f"{new_grade}_{card_pair['unique_id']}_front.{card_pair['extension']}"
    new_back_name = f"{new_grade}_{card_pair['unique_id']}_back.{card_pair['extension']}"
    
    new_front = source_dir / new_front_name
    new_back = source_dir / new_back_name
    
    try:
        # Rename files
        old_front.rename(new_front)
        old_back.rename(new_back)
        
        # Update the card_pair data
        card_pair['grade'] = new_grade
        card_pair['front'] = new_front_name
        card_pair['back'] = new_back_name
        
        st.session_state.classified_count += 1
        
        # Move to next card
        if st.session_state.current_index < len(st.session_state.card_pairs) - 1:
            st.session_state.current_index += 1
        
        return True
    except Exception as e:
        st.error(f"Error renaming files: {str(e)}")
        return False

# Sidebar
st.sidebar.title("🎴 Grade 10 Classifier")

# Load directory section
st.sidebar.header("1. Load Image Directory")
directory_path = st.sidebar.text_input("Image Directory Path", placeholder="/path/to/images/")

if st.sidebar.button("Load Images"):
    if os.path.exists(directory_path):
        with st.spinner("Loading images..."):
            load_image_directory(directory_path)
        st.sidebar.success(f"Loaded {len(st.session_state.card_pairs)} card pairs")
    else:
        st.sidebar.error("Invalid directory path")

# Navigation
if st.session_state.data_loaded:
    st.sidebar.header("2. Navigation")
    total_cards = len(st.session_state.card_pairs)
    
    col1, col2, col3 = st.sidebar.columns(3)
    with col1:
        if st.button("⬅️ Prev"):
            if st.session_state.current_index > 0:
                st.session_state.current_index -= 1
    with col2:
        st.write(f"{st.session_state.current_index + 1}/{total_cards}")
    with col3:
        if st.button("Next ➡️"):
            if st.session_state.current_index < total_cards - 1:
                st.session_state.current_index += 1
    
    # Jump to specific card
    jump_to = st.sidebar.number_input("Jump to card:", min_value=1, max_value=total_cards, value=st.session_state.current_index + 1)
    if st.sidebar.button("Go"):
        st.session_state.current_index = jump_to - 1
    
    # Stats
    st.sidebar.header("Stats")
    st.sidebar.metric("Total Card Pairs", total_cards)
    st.sidebar.metric("Classified", st.session_state.classified_count)
    remaining = total_cards - st.session_state.current_index - 1
    st.sidebar.metric("Remaining", remaining)
    
    # Info
    st.sidebar.header("Info")
    st.sidebar.info("""
    **Classification Guide:**
    - **10m**: Mint condition
    - **10p**: Poor/Problem condition
    
    Only grade 10 and 10.0 cards are shown.
    Both front and back will be renamed.
    """)

# Main content area
if st.session_state.data_loaded:
    if len(st.session_state.card_pairs) == 0:
        st.warning("No card pairs with grade 10/10.0 found in the directory.")
    else:
        current_card = st.session_state.card_pairs[st.session_state.current_index]
        
        st.title(f"Card Classifier - {st.session_state.current_index + 1}/{len(st.session_state.card_pairs)}")
        
        # Card info
        st.subheader(f"Unique ID: {current_card['unique_id']}")
        st.write(f"**Current Grade:** {current_card['grade']}")
        
        st.markdown("---")
        
        # Display front and back images side by side
        col1, col2 = st.columns(2)
        
        source_dir = Path(st.session_state.source_dir)
        
        with col1:
            st.markdown("### 🎴 Front")
            front_path = source_dir / current_card['front']
            if front_path.exists():
                try:
                    img = Image.open(front_path)
                    st.image(img, use_container_width=True)
                    st.caption(current_card['front'])
                except Exception as e:
                    st.error(f"Error loading image: {str(e)}")
            else:
                st.error(f"Image not found: {current_card['front']}")
        
        with col2:
            st.markdown("### 🎴 Back")
            back_path = source_dir / current_card['back']
            if back_path.exists():
                try:
                    img = Image.open(back_path)
                    st.image(img, use_container_width=True)
                    st.caption(current_card['back'])
                except Exception as e:
                    st.error(f"Error loading image: {str(e)}")
            else:
                st.error(f"Image not found: {current_card['back']}")
        
        st.markdown("---")
        
        # Classification buttons
        st.markdown("### Classify this card:")
        
        col1, col2, col3 = st.columns([2, 2, 3])
        
        with col1:
            if st.button("✨ 10m (Mint)", type="primary", use_container_width=True):
                if rename_card_pair(current_card, "10m"):
                    st.success("✅ Classified as 10m (Mint)")
                    st.rerun()
        
        with col2:
            if st.button("⚠️ 10p (Poor)", type="secondary", use_container_width=True):
                if rename_card_pair(current_card, "10p"):
                    st.success("✅ Classified as 10p (Poor)")
                    st.rerun()
        
        with col3:
            # Skip button
            if st.button("⏭️ Skip", use_container_width=True):
                if st.session_state.current_index < len(st.session_state.card_pairs) - 1:
                    st.session_state.current_index += 1
                    st.rerun()
        
        # Keyboard shortcuts hint
        st.markdown("---")
        st.info("💡 **Tip:** Use the Next/Prev buttons in the sidebar to navigate without classifying.")

else:
    # Welcome screen
    st.title("🎴 Card Grade 10 Classifier")
    st.write("""
    ## Welcome!
    
    This application helps you classify grade 10 cards into two categories:
    - **10m**: Mint condition cards
    - **10p**: Poor/Problem condition cards
    
    ### How it works:
    1. Enter the directory path containing your card images in the sidebar
    2. Click "Load Images" to scan for grade 10/10.0 cards
    3. Review each card pair (front and back)
    4. Click either "10m (Mint)" or "10p (Poor)" to classify and rename
    5. Both front and back images will be renamed automatically
    
    ### Filename Format:
    The app expects filenames in this format:
    ```
    GRADE_UNIQUEID_SIDE.EXTENSION
    ```
    
    For example:
    - `10_060701be_front.jpg`
    - `10_060701be_back.jpg`
    - `10.0_c5338e15_front.jpg`
    - `10.0_c5338e15_back.jpg`
    
    ### After Classification:
    Files will be renamed to:
    - `10m_060701be_front.jpg` and `10m_060701be_back.jpg` (if Mint)
    - `10p_060701be_front.jpg` and `10p_060701be_back.jpg` (if Poor)
    
    ### Notes:
    - Only cards with grade exactly 10 or 10.0 are shown
    - Cards must have both front and back images
    - Original files are renamed (not copied)
    - Grade 10.0 will be converted to 10m or 10p (no decimals)
    
    Get started by entering your image directory path in the sidebar! 👈
    """)
