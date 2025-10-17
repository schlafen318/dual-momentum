"""
Asset Universe Manager page for the Streamlit dashboard.

Allows users to create, edit, and manage asset universes.
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, Any, List

from frontend.utils.styling import (
    render_page_header, render_info_box, render_section_divider
)
from frontend.utils.state import save_asset_universes


def render():
    """Render the asset universe manager page."""
    
    render_page_header(
        "Asset Universe Manager",
        "Create and manage predefined asset universes for backtesting",
        "🗂️"
    )
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs([
        "📋 View Universes",
        "➕ Create New",
        "📥 Import/Export"
    ])
    
    with tab1:
        render_view_universes()
    
    with tab2:
        render_create_universe()
    
    with tab3:
        render_import_export()


def render_view_universes():
    """Render view and edit existing universes."""
    
    st.markdown("### 📚 Existing Asset Universes")
    
    universes = st.session_state.asset_universes
    
    if not universes:
        render_info_box("No asset universes defined yet. Create one in the Create New tab!", "info")
        return
    
    # Filter by asset class
    all_asset_classes = list(set(u['asset_class'] for u in universes.values()))
    selected_class_filter = st.selectbox(
        "Filter by asset class",
        ["All"] + sorted(all_asset_classes)
    )
    
    # Display universes
    for name, data in universes.items():
        if selected_class_filter != "All" and data['asset_class'] != selected_class_filter:
            continue
        
        with st.expander(f"🌐 {name} ({data['asset_class'].title()})"):
            render_universe_details(name, data)


def render_universe_details(name: str, data: Dict[str, Any]):
    """Render details and edit controls for a universe."""
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"**Description:** {data.get('description', 'No description')}")
        st.markdown(f"**Asset Class:** {data['asset_class'].title()}")
        st.markdown(f"**Number of Assets:** {len(data['symbols'])}")
        st.markdown(f"**Benchmark:** {data.get('benchmark', 'Not set')}")
    
    with col2:
        if st.button(f"✏️ Edit", key=f"edit_{name}"):
            st.session_state.editing_universe = name
        
        if st.button(f"🗑️ Delete", key=f"delete_{name}"):
            if st.session_state.get('confirm_delete') == name:
                # Delete confirmed
                del st.session_state.asset_universes[name]
                save_asset_universes(st.session_state.asset_universes)
                st.success(f"Deleted universe: {name}")
                del st.session_state.confirm_delete
                st.rerun()
            else:
                # Ask for confirmation
                st.session_state.confirm_delete = name
                st.warning("Click Delete again to confirm")
    
    # Show symbols
    st.markdown("**Assets:**")
    symbols_text = ", ".join(data['symbols'])
    st.code(symbols_text, language=None)
    
    # Edit mode
    if st.session_state.get('editing_universe') == name:
        render_section_divider()
        st.markdown("#### ✏️ Edit Universe")
        
        new_description = st.text_input(
            "Description",
            value=data.get('description', ''),
            key=f"edit_desc_{name}"
        )
        
        new_symbols = st.text_area(
            "Symbols (one per line or comma-separated)",
            value="\n".join(data['symbols']),
            height=150,
            key=f"edit_symbols_{name}"
        )
        
        new_benchmark = st.text_input(
            "Benchmark Symbol",
            value=data.get('benchmark', ''),
            key=f"edit_benchmark_{name}"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 Save Changes", key=f"save_{name}", use_container_width=True):
                # Update universe
                symbols_list = [s.strip() for s in new_symbols.replace(',', '\n').split('\n') if s.strip()]
                
                st.session_state.asset_universes[name].update({
                    'description': new_description,
                    'symbols': symbols_list,
                    'benchmark': new_benchmark if new_benchmark else data.get('benchmark', '')
                })
                
                save_asset_universes(st.session_state.asset_universes)
                st.success(f"Updated universe: {name}")
                del st.session_state.editing_universe
                st.rerun()
        
        with col2:
            if st.button("❌ Cancel", key=f"cancel_{name}", use_container_width=True):
                del st.session_state.editing_universe
                st.rerun()


def render_create_universe():
    """Render form to create new universe."""
    
    st.markdown("### ➕ Create New Asset Universe")
    
    with st.form("create_universe_form"):
        # Universe name
        universe_name = st.text_input(
            "Universe Name *",
            placeholder="e.g., US Tech Stocks",
            help="Unique name for this universe"
        )
        
        # Description
        description = st.text_area(
            "Description",
            placeholder="Brief description of this asset universe",
            height=80
        )
        
        # Asset class
        asset_class = st.selectbox(
            "Asset Class *",
            ["equity", "crypto", "commodity", "bond", "fx"],
            help="Type of assets in this universe"
        )
        
        # Symbols input
        st.markdown("#### 📝 Asset Symbols")
        
        input_method = st.radio(
            "Input Method",
            ["Text Input", "Upload CSV"],
            horizontal=True
        )
        
        symbols_list = []
        
        if input_method == "Text Input":
            symbols_input = st.text_area(
                "Symbols (one per line or comma-separated) *",
                placeholder="AAPL\nMSFT\nGOOGL\nor\nAAPL, MSFT, GOOGL",
                height=150,
                help="Enter asset symbols. One per line or comma-separated."
            )
            
            if symbols_input:
                symbols_list = [s.strip() for s in symbols_input.replace(',', '\n').split('\n') if s.strip()]
        
        else:  # Upload CSV
            uploaded_file = st.file_uploader(
                "Upload CSV with symbols",
                type=['csv'],
                help="CSV file with a 'symbol' column"
            )
            
            if uploaded_file is not None:
                import pandas as pd
                try:
                    df = pd.read_csv(uploaded_file)
                    if 'symbol' in df.columns:
                        symbols_list = df['symbol'].dropna().tolist()
                        st.success(f"Loaded {len(symbols_list)} symbols from CSV")
                    else:
                        st.error("CSV must have a 'symbol' column")
                except Exception as e:
                    st.error(f"Error reading CSV: {str(e)}")
        
        # Benchmark
        benchmark = st.text_input(
            "Benchmark Symbol (optional)",
            placeholder="e.g., SPY",
            help="Reference index or asset for comparison"
        )
        
        # Validation and preview
        if symbols_list:
            st.markdown("#### 👀 Preview")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Asset Class", asset_class.title())
            with col2:
                st.metric("Number of Assets", len(symbols_list))
            with col3:
                st.metric("Benchmark", benchmark if benchmark else "None")
            
            st.markdown("**Symbols:**")
            st.code(", ".join(symbols_list[:10]) + ("..." if len(symbols_list) > 10 else ""))
        
        # Submit button
        submitted = st.form_submit_button("✅ Create Universe", use_container_width=True)
        
        if submitted:
            # Validation
            if not universe_name:
                st.error("Please provide a universe name")
            elif universe_name in st.session_state.asset_universes:
                st.error(f"Universe '{universe_name}' already exists")
            elif not symbols_list:
                st.error("Please provide at least one symbol")
            else:
                # Create universe
                new_universe = {
                    'description': description,
                    'asset_class': asset_class,
                    'symbols': symbols_list,
                    'benchmark': benchmark if benchmark else symbols_list[0],
                    'created_at': datetime.now().isoformat()
                }
                
                st.session_state.asset_universes[universe_name] = new_universe
                save_asset_universes(st.session_state.asset_universes)
                
                st.success(f"✅ Created universe: {universe_name} with {len(symbols_list)} assets")
                st.balloons()


def render_import_export():
    """Render import/export functionality."""
    
    st.markdown("### 💾 Import & Export Universes")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📥 Import Universes")
        
        st.markdown("""
        Import asset universes from a JSON file. The file should contain universe definitions
        in the following format:
        
        ```json
        {
          "Universe Name": {
            "description": "Description",
            "asset_class": "equity",
            "symbols": ["AAPL", "MSFT"],
            "benchmark": "SPY"
          }
        }
        ```
        """)
        
        uploaded_file = st.file_uploader(
            "Upload JSON file",
            type=['json'],
            help="JSON file with universe definitions"
        )
        
        if uploaded_file is not None:
            try:
                imported_universes = json.load(uploaded_file)
                
                # Validate structure
                if not isinstance(imported_universes, dict):
                    st.error("Invalid JSON structure")
                else:
                    st.success(f"Found {len(imported_universes)} universes in file")
                    
                    # Preview
                    with st.expander("Preview imported universes"):
                        st.json(imported_universes)
                    
                    # Merge options
                    merge_option = st.radio(
                        "Import method",
                        ["Merge with existing", "Replace all existing"],
                        help="Choose how to handle existing universes"
                    )
                    
                    if st.button("🔄 Import", use_container_width=True):
                        if merge_option == "Merge with existing":
                            st.session_state.asset_universes.update(imported_universes)
                        else:
                            st.session_state.asset_universes = imported_universes
                        
                        save_asset_universes(st.session_state.asset_universes)
                        st.success("✅ Universes imported successfully!")
                        st.rerun()
                        
            except json.JSONDecodeError:
                st.error("Invalid JSON file")
            except Exception as e:
                st.error(f"Error importing: {str(e)}")
    
    with col2:
        st.markdown("#### 📤 Export Universes")
        
        st.markdown("""
        Export all defined asset universes to a JSON file for backup or sharing.
        """)
        
        if not st.session_state.asset_universes:
            render_info_box("No universes to export", "info")
        else:
            st.metric("Total Universes", len(st.session_state.asset_universes))
            
            # Preview
            with st.expander("Preview universes to export"):
                st.json(st.session_state.asset_universes)
            
            # Export options
            export_format = st.radio(
                "Export format",
                ["JSON (Detailed)", "CSV (Symbols only)"],
                horizontal=True
            )
            
            if export_format == "JSON (Detailed)":
                # Full JSON export
                json_data = json.dumps(st.session_state.asset_universes, indent=2)
                
                st.download_button(
                    label="📥 Download JSON",
                    data=json_data,
                    file_name=f"asset_universes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            else:  # CSV export
                # Create CSV with all universes
                import pandas as pd
                
                csv_data = []
                for name, data in st.session_state.asset_universes.items():
                    for symbol in data['symbols']:
                        csv_data.append({
                            'universe': name,
                            'asset_class': data['asset_class'],
                            'symbol': symbol,
                            'benchmark': data.get('benchmark', '')
                        })
                
                df = pd.DataFrame(csv_data)
                csv_string = df.to_csv(index=False)
                
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_string,
                    file_name=f"asset_universes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    
    render_section_divider()
    
    # Quick templates
    st.markdown("### 📋 Quick Templates")
    
    st.markdown("""
    Start with predefined templates for common asset universe configurations.
    """)
    
    templates = {
        "FAANG Stocks": {
            "description": "Facebook (Meta), Apple, Amazon, Netflix, Google",
            "asset_class": "equity",
            "symbols": ["META", "AAPL", "AMZN", "NFLX", "GOOGL"],
            "benchmark": "QQQ"
        },
        "Major Crypto": {
            "description": "Top 5 cryptocurrencies by market cap",
            "asset_class": "crypto",
            "symbols": ["BTC/USD", "ETH/USD", "BNB/USD", "ADA/USD", "SOL/USD"],
            "benchmark": "BTC/USD"
        },
        "Precious Metals": {
            "description": "Gold, Silver, Platinum, Palladium",
            "asset_class": "commodity",
            "symbols": ["GC", "SI", "PL", "PA"],
            "benchmark": "GC"
        },
        "Treasury Ladder": {
            "description": "US Treasury ETFs across maturities",
            "asset_class": "bond",
            "symbols": ["SHY", "IEI", "IEF", "TLT"],
            "benchmark": "AGG"
        },
        "G7 Currencies": {
            "description": "Major currency pairs vs USD",
            "asset_class": "fx",
            "symbols": ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "USD/CAD"],
            "benchmark": "EUR/USD"
        }
    }
    
    selected_template = st.selectbox(
        "Choose a template",
        ["Select..."] + list(templates.keys())
    )
    
    if selected_template != "Select...":
        template_data = templates[selected_template]
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**{selected_template}**")
            st.caption(template_data['description'])
            st.code(", ".join(template_data['symbols']))
        
        with col2:
            if st.button("➕ Add Template", use_container_width=True):
                # Generate unique name if already exists
                template_name = selected_template
                counter = 1
                while template_name in st.session_state.asset_universes:
                    template_name = f"{selected_template} ({counter})"
                    counter += 1
                
                st.session_state.asset_universes[template_name] = template_data.copy()
                save_asset_universes(st.session_state.asset_universes)
                st.success(f"Added template: {template_name}")
                st.rerun()
