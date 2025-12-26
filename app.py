"""
Climate-Adjusted Multidimensional Poverty Index (MPI) Explorer
Durban, South Africa Case Study
"""

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from models.cells import GeographicCell, ClimateProfile, ContextFactors
from models.mpi import MPICalculator, HouseholdData
from data.climate import ClimateDataFetcher
from data.socioeconomic import SocioeconomicDataLoader

# Page config
st.set_page_config(
    page_title="Climate-Adjusted MPI Explorer",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🌍 Climate-Adjusted Multidimensional Poverty Index")
st.subheader("Durban, South Africa Case Study")

st.markdown("""
This tool demonstrates how climate and geographic context affects poverty measurement.
Traditional MPI uses fixed weights globally - this approach adjusts weights based on local climate conditions.
""")

# Initialize session state
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.census_df = None
    st.session_state.households = None
    st.session_state.climate_stats = None
    st.session_state.cells = None


@st.cache_data
def load_data():
    """Load all required data."""
    with st.spinner("Loading socioeconomic data..."):
        socio_loader = SocioeconomicDataLoader()
        census_df, households = socio_loader.load_or_generate_data(households_per_ward=30)
    
    with st.spinner("Loading climate data..."):
        climate_fetcher = ClimateDataFetcher()
        # Use synthetic data for demo (set force_download=True for real ERA5)
        climate_ds = climate_fetcher.fetch_era5_data(year=2023, force_download=False)
        climate_stats = climate_fetcher.calculate_climate_statistics(climate_ds)
    
    return census_df, households, climate_stats


def create_geographic_cells(census_df: pd.DataFrame, climate_stats: dict) -> list[GeographicCell]:
    """Create GeographicCell objects by matching census and climate data."""
    cells = []
    
    for _, ward in census_df.iterrows():
        lat, lon = ward['latitude'], ward['longitude']
        
        # Find nearest climate grid cell
        # For simplicity, using nearest neighbor
        lat_idx = np.argmin(np.abs(climate_stats['temp_mean'].latitude.values - lat))
        lon_idx = np.argmin(np.abs(climate_stats['temp_mean'].longitude.values - lon))
        
        climate = ClimateProfile(
            avg_temp_range=float(climate_stats['temp_range'].values[lat_idx, lon_idx]),
            heating_degree_days=float(climate_stats['heating_degree_days'].values[lat_idx, lon_idx]),
            cooling_degree_days=float(climate_stats['cooling_degree_days'].values[lat_idx, lon_idx]),
            annual_precipitation=float(climate_stats['annual_precipitation'].values[lat_idx, lon_idx]),
            avg_humidity=float(climate_stats['avg_humidity'].values[lat_idx, lon_idx]) if climate_stats['avg_humidity'] is not None else 70.0,
            temp_min=float(climate_stats['temp_min'].values[lat_idx, lon_idx]),
            temp_max=float(climate_stats['temp_max'].values[lat_idx, lon_idx]),
        )
        
        context = ContextFactors(
            population_density=float(ward['population_density']),
            urban_rural_index=float(ward['urban_rural_index']),
            infrastructure_index=0.7,  # Placeholder
            elevation=0.0,  # Would need DEM data
            distance_to_services=float(ward['distance_to_hospital_km']),
        )
        
        cell = GeographicCell(
            cell_id=ward['ward_id'],
            lat=lat,
            lon=lon,
            name=ward['ward_name'],
            climate=climate,
            context=context,
        )
        
        cells.append(cell)
    
    return cells


# Sidebar - Data Loading
with st.sidebar:
    st.header("Data Configuration")
    
    if st.button("Load Data", type="primary"):
        census_df, households, climate_stats = load_data()
        cells = create_geographic_cells(census_df, climate_stats)
        
        st.session_state.census_df = census_df
        st.session_state.households = households
        st.session_state.climate_stats = climate_stats
        st.session_state.cells = cells
        st.session_state.data_loaded = True
        st.success(f"✓ Loaded {len(cells)} wards, {len(households)} households")
    
    if st.session_state.data_loaded:
        st.metric("Wards", len(st.session_state.cells))
        st.metric("Households", len(st.session_state.households))
        
        st.divider()
        st.header("Visualization Options")
        
        map_metric = st.selectbox(
            "Map Color By",
            ["Climate Harshness", "MPI (Standard)", "MPI (Adjusted)", "MPI Difference", "Temperature Range"]
        )
        
        show_comparison = st.checkbox("Show Standard vs Adjusted Comparison", value=True)


# Main content
if not st.session_state.data_loaded:
    st.info("👈 Click 'Load Data' in the sidebar to begin")
    
    # Show methodology
    with st.expander("📖 Methodology", expanded=True):
        st.markdown("""
        ### How Climate-Adjusted MPI Works
        
        **Standard MPI** uses fixed weights globally:
        - Health: 33.3% (nutrition, child mortality)
        - Education: 33.3% (schooling, attendance)
        - Living Standards: 33.3% (electricity, water, sanitation, housing, fuel, assets)
        
        **Climate-Adjusted MPI** varies weights by context:
        - **Electricity**: Higher weight in harsh climates (heating/cooling critical)
        - **Sanitation/Water**: Higher weight in dense urban areas
        - **Housing**: Higher weight in extreme temperature zones
        - **Core indicators** (nutrition, mortality): Remain relatively constant
        
        **Formula**: `Weight = BaseWeight + (ContextFactor × Adjustment)`
        
        Where context factors are objectively measured:
        - Climate harshness: degree-days from comfort zone (18-24°C)
        - Urbanization: population density + infrastructure
        """)

else:
    # Calculate MPI for all households
    cells_dict = {cell.cell_id: cell for cell in st.session_state.cells}
    
    results = []
    for hh in st.session_state.households:
        cell = cells_dict.get(hh.cell_id)
        if cell:
            adjusted_weights = cell.get_climate_weights()
            comparison = MPICalculator.compare_standard_vs_adjusted(hh, adjusted_weights)
            
            results.append({
                'household_id': hh.household_id,
                'cell_id': hh.cell_id,
                'lat': cell.lat,
                'lon': cell.lon,
                'climate_harshness': cell.climate.climate_harshness,
                'urbanization': cell.context.urbanization_level,
                'standard_score': comparison['standard']['deprivation_score'],
                'adjusted_score': comparison['adjusted']['deprivation_score'],
                'standard_poor': comparison['standard']['is_poor'],
                'adjusted_poor': comparison['adjusted']['is_poor'],
                'score_diff': comparison['difference']['deprivation_score'],
                'classification_changed': comparison['difference']['classification_changed'],
            })
    
    results_df = pd.DataFrame(results)
    
    # Aggregate by cell
    cell_aggregates = results_df.groupby('cell_id').agg({
        'lat': 'first',
        'lon': 'first',
        'climate_harshness': 'first',
        'urbanization': 'first',
        'standard_score': 'mean',
        'adjusted_score': 'mean',
        'standard_poor': 'mean',
        'adjusted_poor': 'mean',
        'score_diff': 'mean',
        'classification_changed': 'sum',
    }).reset_index()
    
    # Add temperature range for mapping
    for idx, row in cell_aggregates.iterrows():
        cell = cells_dict[row['cell_id']]
        cell_aggregates.at[idx, 'temp_range'] = cell.climate.avg_temp_range
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([ "📊 Analysis", "⚖️ Comparison", "🔍 Cell Deep-Dive", "📍 Map View"])
    
    
    with tab1:
        st.header("Statistical Analysis")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Avg Standard MPI",
                f"{results_df['standard_score'].mean():.3f}",
            )
            st.metric(
                "Poverty Rate (Standard)",
                f"{results_df['standard_poor'].mean():.1%}",
            )
        
        with col2:
            st.metric(
                "Avg Adjusted MPI",
                f"{results_df['adjusted_score'].mean():.3f}",
                delta=f"{results_df['score_diff'].mean():+.3f}"
            )
            st.metric(
                "Poverty Rate (Adjusted)",
                f"{results_df['adjusted_poor'].mean():.1%}",
                delta=f"{(results_df['adjusted_poor'].mean() - results_df['standard_poor'].mean()):.1%}"
            )
        
        with col3:
            st.metric(
                "Classification Changes",
                f"{results_df['classification_changed'].sum()} households",
                help="Households that switch poverty status between methods"
            )
            st.metric(
                "Avg Climate Harshness",
                f"{cell_aggregates['climate_harshness'].mean():.2f}",
            )
        
        st.divider()
        
        # Scatter plots
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.scatter(
                results_df,
                x='climate_harshness',
                y='score_diff',
                color='standard_poor',
                title="MPI Difference vs Climate Harshness",
                labels={
                    'climate_harshness': 'Climate Harshness',
                    'score_diff': 'MPI Difference (Adjusted - Standard)',
                    'standard_poor': 'Poor (Standard)',
                },
                trendline="lowess",
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.histogram(
                results_df,
                x='score_diff',
                nbins=50,
                title="Distribution of MPI Differences",
                labels={'score_diff': 'MPI Difference'},
            )
            fig.add_vline(x=0, line_dash="dash", line_color="red")
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("Standard vs Adjusted Comparison")
        
        st.markdown("""
        This view shows how climate adjustment affects poverty classification.
        Points above the diagonal line have **higher** adjusted MPI (more severe when climate considered).
        """)
        
        fig = px.scatter(
            results_df,
            x='standard_score',
            y='adjusted_score',
            color='climate_harshness',
            hover_data=['household_id', 'cell_id'],
            title="Standard MPI vs Climate-Adjusted MPI",
            labels={
                'standard_score': 'Standard MPI Score',
                'adjusted_score': 'Climate-Adjusted MPI Score',
                'climate_harshness': 'Climate Harshness',
            },
        )
        
        # Add diagonal line (y=x)
        max_val = max(results_df['standard_score'].max(), results_df['adjusted_score'].max())
        fig.add_trace(go.Scatter(
            x=[0, max_val],
            y=[0, max_val],
            mode='lines',
            line=dict(dash='dash', color='gray'),
            name='Equal (no change)',
            showlegend=True,
        ))
        
        # Add poverty threshold lines
        fig.add_hline(y=0.33, line_dash="dot", line_color="red", annotation_text="Poverty Threshold")
        fig.add_vline(x=0.33, line_dash="dot", line_color="red")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary stats
        col1, col2 = st.columns(2)
        with col1:
            reclassified_to_poor = ((results_df['standard_poor'] == False) & 
                                    (results_df['adjusted_poor'] == True)).sum()
            st.metric("Reclassified TO Poor", reclassified_to_poor,
                     help="Households not poor by standard MPI but poor when climate-adjusted")
        
        with col2:
            reclassified_to_nonpoor = ((results_df['standard_poor'] == True) & 
                                        (results_df['adjusted_poor'] == False)).sum()
            st.metric("Reclassified FROM Poor", reclassified_to_nonpoor,
                     help="Households poor by standard MPI but not poor when climate-adjusted")

    with tab3:
        st.header("Cell Deep-Dive")
        
        selected_cell_id = st.selectbox(
            "Select Ward",
            options=cell_aggregates['cell_id'].tolist(),
        )
        
        if selected_cell_id:
            cell = cells_dict[selected_cell_id]
            cell_results = results_df[results_df['cell_id'] == selected_cell_id]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Climate Profile")
                st.metric("Climate Harshness", f"{cell.climate.climate_harshness:.2f}")
                st.metric("Heating Degree Days", f"{cell.climate.heating_degree_days:.0f}")
                st.metric("Cooling Degree Days", f"{cell.climate.cooling_degree_days:.0f}")
                st.metric("Temp Range", f"{cell.climate.avg_temp_range:.1f}°C")
                st.metric("Annual Precip", f"{cell.climate.annual_precipitation:.0f} mm")
            
            with col2:
                st.subheader("Context")
                st.metric("Urbanization", f"{cell.context.urbanization_level:.2f}")
                st.metric("Pop Density", f"{cell.context.population_density:.0f}/km²")
                st.metric("Distance to Services", f"{cell.context.distance_to_services:.1f} km")
            
            st.divider()
            
            # Weight comparison
            st.subheader("Indicator Weights")
            
            standard_weights = MPICalculator.STANDARD_WEIGHTS
            adjusted_weights = cell.get_climate_weights()
            
            weight_df = pd.DataFrame({
                'Indicator': list(standard_weights.keys()),
                'Standard': list(standard_weights.values()),
                'Adjusted': [adjusted_weights[k] for k in standard_weights.keys()],
            })
            weight_df['Difference'] = weight_df['Adjusted'] - weight_df['Standard']
            weight_df = weight_df.sort_values('Difference', ascending=False)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name='Standard',
                x=weight_df['Indicator'],
                y=weight_df['Standard'],
            ))
            fig.add_trace(go.Bar(
                name='Adjusted',
                x=weight_df['Indicator'],
                y=weight_df['Adjusted'],
            ))
            fig.update_layout(
                title="Standard vs Adjusted Weights",
                barmode='group',
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Household outcomes
            st.subheader("Household Outcomes in This Ward")
            st.metric("Households", len(cell_results))
            st.metric("Standard Poverty Rate", f"{cell_results['standard_poor'].mean():.1%}")
            st.metric("Adjusted Poverty Rate", f"{cell_results['adjusted_poor'].mean():.1%}")
            st.metric("Classification Changes", int(cell_results['classification_changed'].sum()))
    
    
    with tab4:
        st.header("Geographic Distribution")
        
        # Create map
        center_lat = cell_aggregates['lat'].mean()
        center_lon = cell_aggregates['lon'].mean()
        
        m = folium.Map(location=[center_lat, center_lon], zoom_start=10)
        
        # Determine color metric
        metric_map = {
            "Climate Harshness": 'climate_harshness',
            "MPI (Standard)": 'standard_score',
            "MPI (Adjusted)": 'adjusted_score',
            "MPI Difference": 'score_diff',
            "Temperature Range": 'temp_range',
        }
        
        if 'map_metric' in locals():
            color_by = metric_map[map_metric]
        else:
            color_by = 'climate_harshness'
        
        # Add circles for each cell
        for _, cell_data in cell_aggregates.iterrows():
            value = cell_data[color_by]
            
            # Color scale
            if color_by == 'score_diff':
                # Diverging: red = higher adjusted, blue = lower adjusted
                color = 'red' if value > 0 else 'blue'
                opacity = min(abs(value) * 5, 0.7)
            else:
                # Sequential: darker = higher value
                opacity = min(value, 0.7)
                color = 'red'
            
            folium.Circle(
                location=[cell_data['lat'], cell_data['lon']],
                radius=1000,
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=opacity,
                popup=f"""
                    <b>{cell_data['cell_id']}</b><br>
                    Climate Harshness: {cell_data['climate_harshness']:.2f}<br>
                    Standard MPI: {cell_data['standard_score']:.3f}<br>
                    Adjusted MPI: {cell_data['adjusted_score']:.3f}<br>
                    Difference: {cell_data['score_diff']:+.3f}
                """,
            ).add_to(m)
        
        st_folium(m, width=1200, height=600, returned_objects=[])
        
        # Legend
        st.caption(f"**Color intensity** represents {map_metric}")

# Footer
st.divider()
st.caption("Climate-Adjusted MPI Proof of Concept | Data: Synthetic (based on Durban patterns)")