Mai Shan Yun: Sales & Inventory Intelligence Dashboard

Team: Data Darinde
Avneesh Dubey
Aditya Ghodke
Debmalya Chatterjee
Durgesh Bhirud

Challenge: The Mai Shan Yun Inventory Intelligence Challenge

1. Dashboard's Purpose & Key Insights

The Challenge & Our Analytic Pivot

The hackathon prompt asked for an Inventory Management Dashboard to track ingredients running low, consumption trends, and reorder patterns.

However, the primary dataset available (Final_Data.csv) was a monthly sales summary, lacking the daily transactional, recipe, or shipment data required for a literal inventory-tracking system.

Instead of failing on a technically impossible task, we made a key "Smart Analytic" decision: we treated sales data as a powerful proxy for inventory demand and consumption. This dashboard, therefore, answers the spirit of every challenge question by providing deep, actionable insights on menu performance, which is the #1 driver of all inventory decisions.

Key Insights (Our 4-Point Action Plan)

Our dashboard analyzes 6 months of sales data to generate an "Executive Summary" with the following actionable insights:

Focus Your Efforts (The 80/20 Rule): Our Pareto analysis shows that your Top 21 items (just 13.0% of your menu) drive 80% of your revenue. Managers should focus their quality control and inventory planning almost exclusively on these critical items.

Protect Your Superstar: 'Beef Ramen' is your #1 item. You must never run out of the ingredients for this dish.

Reorder Alert (Rising Star): 'Mai's BF Chicken Cutlet Combo' is your fastest-growing item. Increase your stock of its ingredients now to meet rising demand.

Overstock Alert (Fading Item): 'Strawberry Sunrise Tea' is declining fast. Reduce purchase orders for its unique ingredients to prevent waste and consider a promotion.

2. Datasets Used & Data Handling

Datasets

Primary: Final_Data.csv
 Final_Data.csv was Obtained after pre=processing our original datasets containing CSVs with Ingredients and Shipments and XLSX files of monthly sales from May to October. We merged all our datasets into the Final_Data.csv which finally had the following fields:
source_page	source_table	Item Name	Count	Amount	Month


Reasoning: This was the only clean, complete, and reliable dataset provided. The other files (Ingredient.csv, Shipment.csv, and the 6 monthly .xlsx files) were either missing, incomplete, or—upon inspection—also monthly summaries, making a true inventory-flow calculation impossible. Our entire solution is built on a robust analysis of this single source of truth.

Data Integration & Feature Engineering

Our dashboard isn't just plotting a CSV; it's performing several key data-handling steps to generate new insights:

Data Cleaning: We converted Amount (e.g., "$6,921.26") and Count (e.g., "1,000") columns from text to numeric types, making them analyzable.

Feature Engineering (Categorization): We built a custom function to parse Item Name strings (e.g., "Steam Pork Dumplings") and intelligently categorize them (e.g., "Appetizers"). This fixed data-entry errors (like "Steam" being classified as "Tea") and unlocked our bundling insights via the Treemap.

Time-Based Aggregation: We created a "Movers & Shakers" analysis by splitting the 6-month period in half (May-Jul vs. Aug-Oct) and calculating the percentage growth/decline for every item.

Statistical Aggregation: We built the Pareto and Quadrant plots by aggregating all items by their total sales, count, and average price.

3. Setup and Run Instructions

This dashboard is a self-contained Streamlit web application.

Prerequisites

Python 3.8 - 3.11

pip (Python package installer)

Installation

Clone or download the project folder.

Place your Final_Data.csv file in the same directory as the mai_shan_yun_app.py script.

Open your terminal, navigate to the project folder, and install the required libraries:

pip install streamlit pandas plotly


Running the Dashboard

In your terminal, run the following command:

streamlit run mai_shan_yun_app.py


Your web browser will automatically open to the dashboard.

4. Example Insights & Use Cases

This dashboard is designed to be an interactive decision-making tool for a restaurant manager.

Use Case 1: The "What-If" Scenario Planner

Question: "I want to run a promotion on 'Pork Tossed Ramen,' but is it worth it?"

Action: The manager uses the "What-If" Menu Item Planner at the bottom of the dashboard.

They select "Pork Tossed Ramen" from the dropdown.

They drag the "Simulate Change in Quantity Sold" slider to +30%.

They drag the "Simulate Change in Price" slider to -15%.

Result: They watch the "Pork Tossed Ramen" bubble on the Quadrant Plot move in real-time, seeing if it shifts from a "Workhorse" (high sales, low profit) to a "Star" (high sales, high profit). This tool allows them to test any promotion idea instantly.

Use Case 2: The "Reorder Alert"

Question: "Which ingredients do I need to reorder urgently?"

Action: The manager looks at the "Rising Stars" plot.

Result: They see that "Mai's BF Chicken Cutlet Combo" sales are growing rapidly. This acts as a proxy "reorder alert," telling them to increase their purchase order for chicken and cutlets.

Use Case 3: The "Overstock Alert"

Question: "What am I wasting money on?"

Action: The manager looks at the "Fading Items" plot.

Result: They see "Strawberry Sunrise Tea" is in steep decline. This is an "overstock alert," warning them to reduce their stock of its unique ingredients (e.g., strawberry puree) to cut costs and prevent waste.

Use Case 4: The "Bundling Opportunity"

Question: "How can I increase my average order value?"

Action: The manager looks at the "Revenue Breakdown" Treemap.


Result: They instantly see that "Noodle Dishes" and "Rice Dishes" make up the vast majority of their sales, while "Drinks" and "Appetizers" are tiny categories. This provides a clear, data-driven insight to create a "Combo" or "Bundle" (e.g., "Noodle Dish + Drink for $2 more") to boost the sales of their high-margin, low-performing categories.
