import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
import numpy as np
import streamlit as st

# Suppress warnings
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)

# --- 0. Dashboard Design & Theme ---
DASHBOARD_TEMPLATE = 'plotly_dark'
BRAND_COLOR = '#FFBF00' # Gold
POSITIVE_COLOR = '#059669' # Green
NEGATIVE_COLOR = '#E11D48' # Red
FONT_FAMILY = "Arial"

# --- 1. Load, Clean, and FEATURE ENGINEER ---

@st.cache_data # Cache the data loading
def categorize_item(item_name):
    """
    Applies business logic to categorize items.
    *** UPDATED LOGIC TO FIX CLASSIFICATION ***
    """
    item_name_low = item_name.lower()
    
    # 1. Appetizers (Check first to catch 'steam' before 'tea')
    if any(app in item_name_low for app in [
        'dumpling', 'wings', 'tenders', 'roll', 'crab', 'rangoon', 'bun', 'steam'
    ]):
        return 'Appetizers'
        
    # 2. Noodles
    if 'ramen' in item_name_low or 'noodle' in item_name_low:
        return 'Noodle Dishes'
        
    # 3. Rice
    if 'rice' in item_name_low:
        return 'Rice Dishes'
        
    # 4. Combos
    if 'combo' in item_name_low or 'special' in item_name_low:
        return 'Combos/Specials'
        
    # 5. Drinks (Check last, now that 'steam' is handled)
    if any(drink in item_name_low for drink in ['tea', 'lemonade', 'soda', 'coke', 'pepsi', 'starry', 'crush']):
        return 'Drinks'
    
    # Default category
    return 'Other Entrees'

@st.cache_data # Cache the data loading
def load_and_clean_data(filepath="Final_Data.csv"):
    """
    Loads, cleans, and enriches the data with a new 'Category' column.
    This is the only usable file.
    """
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        st.error(f"Error: {filepath} not found. Please make sure Final_Data.csv is in the same folder.")
        return None

    # Clean Amount
    df['Amount'] = df['Amount'].replace({r'\$': '', ',': ''}, regex=True).astype(float)
    # Clean Count
    df['Count'] = pd.to_numeric(df['Count'].replace({',': ''}, regex=True), errors='coerce').fillna(0).astype(int)
    
    # Define month order
    month_order = ['May', 'June', 'July', 'August', 'September', 'October']
    df['Month'] = pd.Categorical(df['Month'], categories=month_order, ordered=True)
    
    # *** NEW FEATURE ENGINEERING ***
    df['Category'] = df['Item Name'].apply(categorize_item)
    
    print("Data loaded, cleaned, and categorized successfully.")
    return df

@st.cache_data
def get_item_summary(df):
    """
    Helper function to get the base summary data for what-if analysis.
    """
    item_summary = df.groupby('Item Name').agg(
        Total_Amount=('Amount', 'sum'),
        Total_Count=('Count', 'sum')
    ).reset_index()
    
    # Add a small epsilon to avoid division by zero if count is 0
    item_summary['Avg_Price'] = (item_summary['Total_Amount'] / (item_summary['Total_Count'] + 1e-6)).fillna(0)
    return item_summary

# --- 2. Generate Visualizations (Polished Plots) ---

def apply_global_styles(fig, title):
    """
    Applies our consistent "beautify" styles to every plot.
    """
    fig.update_layout(
        title_text=title,
        title_x=0.5, # Center the title
        template=DASHBOARD_TEMPLATE,
        font=dict(family=FONT_FAMILY, color='white'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    return fig

def make_plot1_sales_per_month(df):
    """ PLOT 1: Total Sales per Month (Bar Chart) """
    sales_per_month = df.groupby('Month')['Amount'].sum().reset_index()
    
    fig = px.bar(
        sales_per_month, x='Month', y='Amount',
        labels={'Amount': 'Total Sales ($)'}, text_auto='.2s'
    )
    fig.update_traces(marker_color=BRAND_COLOR, textposition='outside')
    fig = apply_global_styles(fig, 'Total Revenue Trend (Proxy for Monthly Usage)')
    fig.update_layout(yaxis_title='Total Revenue ($)', xaxis_title='Month')
    return fig

def make_plot2_top_10_items(df):
    """ PLOT 2: Top 10 Revenue-Generating Items (Bar Chart) """
    top_10_items = df.groupby('Item Name')['Amount'].sum().nlargest(10).reset_index()

    fig = px.bar(
        top_10_items, x='Item Name', y='Amount',
        labels={'Amount': 'Total Revenue ($)', 'Item Name': 'Menu Item'},
        text_auto='.2s'
    )
    fig.update_traces(marker_color=BRAND_COLOR)
    fig = apply_global_styles(fig, 'Top 10 Revenue-Driving Items (Core Inventory)')
    fig.update_layout(
        xaxis={'categoryorder':'total descending'}, 
        yaxis_title='Total Revenue ($)', xaxis_title='Menu Item'
    )
    return fig, top_10_items

def make_plot3_what_if_quadrant(item_summary_df, item_to_change, count_change_pct, price_change_pct):
    """ 
    PLOT 3: *** "WHAT-IF" VERSION ***
    This function takes the what-if inputs and returns the modified plot.
    """
    
    df_what_if = item_summary_df.copy()
    
    try:
        item_row = df_what_if[df_what_if['Item Name'] == item_to_change].iloc[0]
    except IndexError:
        st.error(f"Could not find item '{item_to_change}' to model.")
        return go.Figure()

    # Apply "what-if" logic
    new_count = item_row['Total_Count'] * (1 + count_change_pct / 100)
    new_price = item_row['Avg_Price'] * (1 + price_change_pct / 100)
    new_amount = new_count * new_price
    
    df_what_if.loc[df_what_if['Item Name'] == item_to_change, 'Total_Count'] = new_count
    df_what_if.loc[df_what_if['Item Name'] == item_to_change, 'Total_Amount'] = new_amount
    df_what_if.loc[df_what_if['Item Name'] == item_to_change, 'Avg_Price'] = new_price
    
    median_amount = df_what_if['Total_Amount'].median()
    median_count = df_what_if['Total_Count'].median()

    fig = go.Figure()
    
    # Add all other items
    fig.add_trace(go.Scatter(
        x=df_what_if[df_what_if['Item Name'] != item_to_change]['Total_Count'], 
        y=df_what_if[df_what_if['Item Name'] != item_to_change]['Total_Amount'],
        mode='markers',
        name='Other Items',
        marker=dict(
            size=df_what_if['Total_Amount'] / 2000, sizemin=4, sizemode='diameter',
            color=df_what_if['Avg_Price'], colorscale='Viridis',
            showscale=True, colorbar=dict(title='Avg. Price ($)'),
            opacity=0.5 
        ),
        text=df_what_if['Item Name'],
        hovertemplate=(
            "<b>%{text}</b><br>" +
            "Total Sold: %{x:,.0f}<br>" +
            "Total Revenue: $%{y:,.2f}<br>" +
            "Avg. Price: $%{marker.color:,.2f}" +
            "<extra></extra>"
        )
    ))
    
    # Add the "What-If" item (larger, brighter)
    what_if_item = df_what_if[df_what_if['Item Name'] == item_to_change]
    fig.add_trace(go.Scatter(
        x=what_if_item['Total_Count'], 
        y=what_if_item['Total_Amount'],
        mode='markers',
        name=f'WHAT-IF: {item_to_change}',
        marker=dict(
            size=what_if_item['Total_Amount'] / 2000, sizemin=4, sizemode='diameter',
            color=what_if_item['Avg_Price'], colorscale='Viridis',
            line=dict(color=BRAND_COLOR, width=3), 
            opacity=1.0
        ),
        text=what_if_item['Item Name'],
        hovertemplate=(
            "<b>%{text} (WHAT-IF)</b><br>" +
            "Total Sold: %{x:,.0f}<br>" +
            "Total Revenue: $%{y:,.2f}<br>" +
            "Avg. Price: $%{marker.color:,.2f}" +
            "<extra></extra>"
        )
    ))

    # Add quadrant lines
    fig.add_shape(type="line", x0=median_count, y0=0, x1=median_count, y1=df_what_if['Total_Amount'].max(), line=dict(color="Gray", width=2, dash="dash"))
    fig.add_shape(type="line", x0=0, y0=median_amount, x1=df_what_if['Total_Count'].max(), y1=median_amount, line=dict(color="Gray", width=2, dash="dash"))
    
    # Add quadrant labels
    fig.add_annotation(x=df_what_if['Total_Count'].max(), y=df_what_if['Total_Amount'].max(), text="<b>STARS</b><br>(High Sales, High Profit)", showarrow=False, xanchor='right', yanchor='top', font=dict(color='white', size=14))
    fig.add_annotation(x=0, y=df_what_if['Total_Amount'].max(), text="<b>NICHE/PREMIUM</b><br>(Low Sales, High Profit)", showarrow=False, xanchor='left', yanchor='top', font=dict(color='white', size=14))
    fig.add_annotation(x=df_what_if['Total_Count'].max(), y=0, text="<b>WORKHORSES</b><br>(High Sales, Low Profit)", showarrow=False, xanchor='right', yanchor='bottom', font=dict(color='white', size=14))
    fig.add_annotation(x=0, y=0, text="<b>DOGS</b><br>(Low Sales, Low Profit)", showarrow=False, xanchor='left', yanchor='bottom', font=dict(color='white', size=14))

    fig = apply_global_styles(fig, 'Item Analysis: "What-If" Scenario')
    fig.update_layout(
        xaxis_title='Total Units Sold (Popularity)', yaxis_title='Total Revenue ($)',
        height=700,
        legend=dict(y=1.1) 
    )
    return fig

def make_plot4_top_10_trends(df, top_10_item_names):
    """ PLOT 4: Monthly Sales Trends for Top 10 Items (Line Chart) """
    month_order = ['May', 'June', 'July', 'August', 'September', 'October']
    df_top_10 = df[df['Item Name'].isin(top_10_item_names)]
    monthly_sales_top_10 = df_top_10.groupby(['Month', 'Item Name'])['Amount'].sum().reset_index()
    monthly_sales_top_10['Month'] = pd.Categorical(monthly_sales_top_10['Month'], categories=month_order, ordered=True)
    monthly_sales_top_10 = monthly_sales_top_10.sort_values('Month')

    fig = px.line(
        monthly_sales_top_10,
        x='Month', y='Amount', color='Item Name',
        labels={'Amount': 'Monthly Sales ($)', 'Item Name': 'Menu Item'},
        markers=True
    )
    
    if top_10_item_names:
        top_item = top_10_item_names[0] 
        for trace in fig.data:
            if trace.name == top_item:
                trace.update(line=dict(width=4))
            else:
                trace.update(opacity=0.5)

    fig = apply_global_styles(fig, 'Monthly Consumption Trends (by Item Revenue)')
    
    # --- FIX #2: Reposition legend to prevent overlap ---
    fig.update_layout(
        legend=dict(
            orientation="h",    # Horizontal legend
            yanchor="bottom",   # Anchor to the bottom
            y=-0.3,             # Position it *below* the x-axis
            xanchor="center",   # Center it
            x=0.5
        ),
        xaxis_title='Month', 
        yaxis_title='Monthly Revenue ($)'
    )
    return fig, monthly_sales_top_10

def make_plot5_category_treemap(df):
    """ PLOT 5: Revenue by Menu Category (Treemap) """
    fig = px.treemap(
        df,
        path=[px.Constant("All Items"), 'Category', 'Item Name'],
        values='Amount',
        color='Category', 
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    
    fig.update_traces(
        hovertemplate='<b>%{label}</b><br>Sales: $%{value:,.2f}<br>% of Parent: %{percentParent:.1%}',
        textinfo="label+percent parent" 
    )
    
    fig = apply_global_styles(fig, 'Revenue Breakdown by Menu Category and Item')
    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))
    return fig

def make_plot6_movers_and_shakers(df):
    """ PLOT 6: "Movers & Shakers" (Percent Growth Bar Charts) """
    first_half = df[df['Month'].isin(['May', 'June', 'July'])]
    second_half = df[df['Month'].isin(['August', 'September', 'October'])]
    first_half_sales = first_half.groupby('Item Name')['Amount'].sum()
    second_half_sales = second_half.groupby('Item Name')['Amount'].sum()
    growth_df = pd.DataFrame({'First_Half': first_half_sales, 'Second_Half': second_half_sales}).fillna(0)
    
    # Calculate % Growth, handle division by zero
    growth_df['Growth_Pct'] = 100 * (growth_df['Second_Half'] - growth_df['First_Half']) / (growth_df['First_Half'] + 1e-6)
    
    growth_df['Total_Sales'] = growth_df['First_Half'] + growth_df['Second_Half']
    growth_df = growth_df.replace([np.inf, -np.inf], np.nan)
    growth_df = growth_df[growth_df['Total_Sales'] > 500] 
    growth_df = growth_df.dropna()
    rising_stars = growth_df.nlargest(10, 'Growth_Pct').reset_index()
    fading_items = growth_df.nsmallest(10, 'Growth_Pct').reset_index()

    fig_rising = px.bar(
        rising_stars,
        x='Item Name', y='Growth_Pct',
        labels={'Growth_Pct': 'Growth (%)', 'Item Name': 'Menu Item'},
        text_auto='.1f'
    )
    fig_rising.update_traces(marker_color=POSITIVE_COLOR) 
    fig_rising = apply_global_styles(fig_rising, '"Rising Stars" (Reorder Alert: High Growth)')
    fig_rising.update_layout(xaxis={'categoryorder':'total descending'}, yaxis_title='Growth (%)')

    fig_fading = px.bar(
        fading_items,
        x='Item Name', y='Growth_Pct',
        labels={'Growth_Pct': 'Growth (%)', 'Item Name': 'Menu Item'},
        text_auto='.1f'
    )
    fig_fading.update_traces(marker_color=NEGATIVE_COLOR) 
    fig_fading = apply_global_styles(fig_fading, '"Fading Items" (Overstock Alert: High Decline)')
    fig_fading.update_layout(xaxis={'categoryorder':'total ascending'}, yaxis_title='Growth (%)')
    
    return fig_rising, fig_fading, rising_stars, fading_items

def make_plot7_pareto_analysis(df):
    """ PLOT 7: Pareto Analysis (80/20 Rule) - DE-CLUTTERED """
    item_sales = df.groupby('Item Name')['Amount'].sum().reset_index()
    item_sales = item_sales.sort_values(by='Amount', ascending=False)
    
    N_TOP_ITEMS = 20 
    
    if len(item_sales) > N_TOP_ITEMS:
        df_top_n = item_sales.head(N_TOP_ITEMS)
        df_other = item_sales.tail(-N_TOP_ITEMS)
        other_row = pd.DataFrame({'Item Name': ['All Other Items'], 'Amount': [df_other['Amount'].sum()]})
        pareto_df = pd.concat([df_top_n, other_row]).reset_index(drop=True)
    else:
        pareto_df = item_sales
    
    total_revenue = pareto_df['Amount'].sum()
    pareto_df['Cumulative_Amount'] = pareto_df['Amount'].cumsum()
    pareto_df['Cumulative_Pct'] = 100 * pareto_df['Cumulative_Amount'] / total_revenue
    
    total_items = len(item_sales) 
    
    pareto_summary = "Pareto analysis incomplete (insufficient item diversity)."
    if not pareto_df[pareto_df['Cumulative_Pct'] >= 80].empty:
        try:
            num_items_for_80 = pareto_df[pareto_df['Cumulative_Pct'] >= 80].index[0] + 1
            pct_items = 100 * num_items_for_80 / total_items
            pareto_summary = f"Your Top {num_items_for_80} items (just {pct_items:.1f}% of your menu) drive 80% of your revenue."
        except IndexError:
             pareto_summary = "Pareto analysis incomplete."

    print(f"\nPARETO ANALYSIS: {pareto_summary}\n")

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=pareto_df['Item Name'], y=pareto_df['Amount'],
            name='Revenue per Item', marker_color=BRAND_COLOR
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=pareto_df['Item Name'], y=pareto_df['Cumulative_Pct'],
            name='Cumulative Revenue %', mode='lines+markers', marker_color=NEGATIVE_COLOR
        ),
        secondary_y=True,
    )
    fig.add_hline(
        y=80, line_dash="dash", line_color="white", 
        annotation_text="80% Mark", annotation_position="bottom left",
        secondary_y=True
    )
    fig = apply_global_styles(fig, f'Pareto Analysis (80/20 Rule): {pareto_summary}')
    fig.update_layout(
        xaxis_title='Menu Items (Ranked by Revenue)',
        xaxis=dict(ticks=""), 
        height=600
    )
    fig.update_yaxes(title_text="Total Revenue ($)", secondary_y=False)
    fig.update_yaxes(title_text="Cumulative Revenue (%)", secondary_y=True, range=[0, 105])

    return fig, pareto_summary

# --- 4. AI Analytics Prompt Generation (REMOVED) ---
# This section has been removed as requested.

# --- 5. Main Streamlit App Execution ---

def main():
    # --- Page Configuration ---
    st.set_page_config(
        page_title="Mai Shan Yun Dashboard", # Changed
        page_icon="🍜",
        layout="wide" # Use the full width of the page
    )

    # --- Change 1: Removed "AI-Powered" ---
    st.title("🍜 Mai Shan Yun Inventory Dashboard")
    st.markdown("Turning 6 months of sales data into actionable business intelligence.")

    # --- Load Data ---
    df = load_and_clean_data()
    if df is None:
        return
    
    # --- Pre-calculate all dataframes ---
    item_summary_df = get_item_summary(df)
    fig1 = make_plot1_sales_per_month(df)
    fig2, top_10_items = make_plot2_top_10_items(df)
    fig4, monthly_sales_top_10 = make_plot4_top_10_trends(df, top_10_items['Item Name'].tolist())
    fig5 = make_plot5_category_treemap(df)
    fig6_rising, fig6_fading, rising_stars, fading_items = make_plot6_movers_and_shakers(df)
    fig7, pareto_summary = make_plot7_pareto_analysis(df)
    
    
    # --- NEW LAYOUT ---
    st.divider()

    # --- Executive Summary ---
    # --- Change 2: Removed "AI-Powered" from subheader ---
    st.subheader("🤖 Executive Summary")
    
    # --- Change 3: Removed placeholder text ---
    
    with st.spinner("Generating analysis..."):
        
        try:
            pareto_str = pareto_summary
            superstar_str = top_10_items.iloc[0]['Item Name'] if not top_10_items.empty else "N/A"
            rising_str = rising_stars.iloc[0]['Item Name'] if not rising_stars.empty else "N/A (no significant rising stars)"
            fading_str = fading_items.iloc[0]['Item Name'] if not fading_items.empty else "N/A (no significant fading items)"
        except Exception as e:
            st.warning(f"Could not generate full summary: {e}")
            pareto_str = "Analysis pending."
            superstar_str = "N/A"
            rising_str = "N/A"
            fading_str = "N/A"

        # --- Change 4: Updated info box title ---
        st.info(
            f"**Your 4-Point Action Plan (Proxy for Inventory Insights):**\n"
            f"* **Focus Your Efforts:** {pareto_str} Stop worrying about the bottom 80% of your menu and focus on the ingredients for these critical items.\n"
            f"* **Protect Your Superstar:** '{superstar_str}' is your #1 item. **Never** run out of the ingredients for this dish.\n"
            f"* **Reorder Alert (Rising Star):** '{rising_str}' is your fastest-growing item. Increase your stock of its ingredients now.\n"
            f"* **Overstock Alert (Fading Item):** '{fading_str}' is declining fast. Reduce purchase orders for its unique ingredients."
        )

        # --- Change 5: Removed the expander ---

    st.divider()

    # --- Full Dashboard Layout ---
    st.subheader("Restaurant Performance Deep Dive (May-Oct)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig1, use_container_width=True) # Sales per Month
    with col2:
        st.plotly_chart(fig2, use_container_width=True) # Top 10 Items
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.plotly_chart(fig7, use_container_width=True) # Pareto
    with col2:
        st.plotly_chart(fig5, use_container_width=True) # Treemap
        
    st.plotly_chart(fig4, use_container_width=True) # Top 10 Trends
    
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig6_rising, use_container_width=True) # Rising Stars
    with col2:
        st.plotly_chart(fig6_fading, use_container_width=True) # Fading Items

    st.divider()

    # --- *** "What-If" Analysis Module (NOW AT THE BOTTOM) *** ---
    st.subheader('📈 "What-If" Menu Item Planner')
    st.markdown("Use these sliders to see how changing a product's price or sales impacts its position in the menu. This helps you plan promotions and stocking priorities.")

    item_list = item_summary_df['Item Name'].unique()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        # Default to 'Beef Ramen' if it exists, otherwise default to the first item
        default_index = 0
        if "Beef Ramen" in item_list:
            default_index = list(item_list).index("Beef Ramen")
            
        item_to_change = st.selectbox(
            "Select an Item to Model:",
            item_list,
            index=default_index 
        )
    with col2:
        count_change_pct = st.slider(
            "Simulate Change in Quantity Sold (e.g., a promotion)",
            min_value=-50, max_value=100, value=0, step=5, format="%d%%"
        )
    with col3:
        price_change_pct = st.slider(
            "Simulate Change in Price",
            min_value=-50, max_value=100, value=0, step=5, format="%d%%"
        )

    fig3_what_if = make_plot3_what_if_quadrant(item_summary_df, item_to_change, count_change_pct, price_change_pct)
    st.plotly_chart(fig3_what_if, use_container_width=True)
    


if __name__ == "__main__":
    main()