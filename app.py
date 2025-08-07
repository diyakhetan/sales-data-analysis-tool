import streamlit as st
import pandas as pd

from exceptions_tab import show_exceptions_tab  # custom module
from reports import show_reports_tab
from reports import show_forecast_tab
from faq_bot import show_faq_tab





st.set_page_config(page_title="Sales ETL & Exceptions", layout="wide")
st.title("Sales Data Analysis Tool")

if 'merged_df' not in st.session_state:
    st.session_state.merged_df = None


# Top-level tabs
tab1, tab2,tab3,tab4,tab5 = st.tabs(["📊 ETL Pipeline", "🚨 Exceptions & Anomalies","📁 Reports","Forecasting","FAQ Bot"])

@st.cache_data(show_spinner=False)
def load_csv(file):
    return pd.read_csv(file)

# Shared state
if "mapped_df" not in st.session_state:
    st.session_state.mapped_df = None

# ETL PIPELINE TAB
with tab1:

    # Step 1: Upload Original Dataset
    st.header("1. Upload Your Primary CSV File")
    uploaded_file = st.file_uploader("Choose the primary CSV file", type="csv")

    if uploaded_file:
        df = load_csv(uploaded_file)
        st.write("Preview of Primary Dataset", df.head())

        # Step 2: Upload Secondary Dataset and Map Columns
        st.header("2. Upload Secondary CSV to Map Columns")
        uploaded_file_2 = st.file_uploader("Upload secondary CSV file", type="csv", key="second_file")

        if uploaded_file_2:
            user_df = load_csv(uploaded_file_2)
            st.write("Preview of Secondary Dataset", user_df.head())

            st.subheader("Map Columns from Secondary Dataset to Primary Dataset")

            mapping = {}
            for col in user_df.columns:
                mapped_col = st.selectbox(
                    f"Map '{col}' to column in primary dataset:",
                    options=["-- None --"] + list(df.columns),
                    key=f"map_{col}"
                )
                if mapped_col != "-- None --":
                    mapping[col] = mapped_col

            st.write("Selected Mappings:", mapping)

            if mapping:
                mapped_df = user_df.rename(columns=mapping)

                st.subheader("Preview of Mapped Secondary Dataset")
                st.write(mapped_df.head())

                # --- Nulls in full mapped dataset
                st.subheader("Null Value Check in Mapped Dataset")
                if mapped_df.isnull().values.any():
                    st.warning("⚠️ The mapped dataset contains missing (null) values.")
                    st.dataframe(mapped_df.isnull().sum().reset_index().rename(columns={'index': 'Column', 0: 'Null Count'}))
                else:
                    st.success("✅ No missing values found in the mapped dataset.")

                
                # --- Null Handling
                st.subheader("Handle Missing Values in Mapped Dataset")

                if mapped_df.isnull().values.any():
                    null_summary = mapped_df.isnull().sum()
                    null_columns = null_summary[null_summary > 0]

                    for col in null_columns.index:
                        st.markdown(f"**Column:** `{col}` — {null_columns[col]} missing value(s)")

                        if pd.api.types.is_numeric_dtype(mapped_df[col]):
                            option = st.selectbox(
                                f"Handle nulls in numeric column '{col}':",
                                options=["Ignore rows", "Fill with mean", "Fill with mode"],
                                key=f"null_option_{col}"
                            )
                        else:
                            option = st.selectbox(
                                f"Handle nulls in non-numeric column '{col}':",
                                options=["Ignore rows", "Fill with mode"],
                                key=f"null_option_{col}"
                            )

                        if option == "Ignore rows":
                            mapped_df = mapped_df[mapped_df[col].notna()]
                        elif option == "Fill with mean":
                            mapped_df[col].fillna(mapped_df[col].mean(), inplace=True)
                        elif option == "Fill with mode":
                            mode_val = mapped_df[col].mode()
                            if not mode_val.empty:
                                mapped_df[col].fillna(mode_val[0], inplace=True)
                else:
                    st.success("✅ No missing values found in the mapped dataset.")


                # --- Download full mapped dataset
                st.subheader("Download Mapped Dataset")
                mapped_csv = mapped_df.to_csv(index=False).encode('utf-8')
                st.download_button("Download Mapped CSV", mapped_csv, file_name="mapped_dataset.csv", mime='text/csv')

                st.subheader("Update Original Dataset with Mapped Columns")

                update_option = st.checkbox("Update original dataset with mapped columns")

                if update_option:
                    # Avoid duplicate column names
                    new_cols = [col for col in mapped_df.columns if col not in df.columns]
                    
                    if new_cols:
                        updated_df = pd.concat([df.reset_index(drop=True), mapped_df[new_cols].reset_index(drop=True)], axis=1)
                        st.success("Original dataset updated with mapped columns.")
                        st.write("Preview of Updated Dataset", updated_df.head())

                        updated_csv = updated_df.to_csv(index=False).encode('utf-8')
                        st.download_button("Download Updated Dataset", updated_csv, file_name="updated_dataset.csv", mime='text/csv')
                    else:
                        st.warning("No new columns found to add from mapped dataset.")


                # Step 3: Filtering
                st.header("3. Filter Mapped Data")

                if 'State' in mapped_df.columns:
                    states = sorted(mapped_df['State'].dropna().unique())

                    if 'selected_states' not in st.session_state:
                        st.session_state.selected_states = states

                    select_all = st.checkbox("Select all States", value=True)

                    if select_all:
                        st.session_state.selected_states = states
                    else:
                        st.session_state.selected_states = st.multiselect(
                            "Filter by State(s)", states, default=st.session_state.get("selected_states", [])
                        )

                    selected_states = st.session_state.selected_states

                    if selected_states:
                        mapped_df = mapped_df[mapped_df['State'].isin(selected_states)]
                    else:
                        st.warning("No state selected. Please select at least one to view data.")
                        mapped_df = pd.DataFrame()
                else:
                    st.warning("'State' column not found in mapped dataset.")

                # Numeric filter
                numeric_cols = mapped_df.select_dtypes(include='number').columns.tolist()

                if numeric_cols and not mapped_df.empty:
                    col_to_filter = st.selectbox("Select numeric column to filter", numeric_cols)

                    if col_to_filter in ['Sales Amt', 'Qty']:
                        threshold = st.slider(
                            f"Select minimum value for {col_to_filter}",
                            int(mapped_df[col_to_filter].min()),
                            int(mapped_df[col_to_filter].max())
                        )
                        filtered_df = mapped_df[mapped_df[col_to_filter] > threshold]
                    else:
                        unique_vals = sorted(mapped_df[col_to_filter].dropna().unique())
                        selected_vals = st.multiselect(
                            f"Select values to filter for {col_to_filter}",
                            options=unique_vals,
                            default=unique_vals
                        )
                        filtered_df = mapped_df[mapped_df[col_to_filter].isin(selected_vals)].head(1000)

                    # Combine original df and mapped_df horizontally (side-by-side) or vertically (stacked)
                    merged_df = pd.concat([df.reset_index(drop=True), mapped_df.reset_index(drop=True)], axis=1)

                    # Optional: Drop duplicate columns (if mapped_df had renamed overlaps)
                    merged_df = merged_df.loc[:, ~merged_df.columns.duplicated()]

                    # Store in session for use in reports tab
                    st.session_state.merged_df = merged_df

                    st.write(f"Filtered Data", filtered_df)
                
                    # Download filtered data
                    st.subheader("Download Filtered Data")
                    csv = filtered_df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download Filtered CSV", csv, file_name="filtered_mapped_data.csv", mime='text/csv')

                else:
                    st.warning("No numeric columns found or no data available after filtering.")
            else:
                st.info("No mappings selected yet.")
        else:
            #st.info("Upload a secondary CSV file to proceed with mapping and filtering.")
            if 'State' in df.columns:
                states = sorted(df['State'].dropna().unique())
                selected_states = st.multiselect("Filter by State(s)", states, default=states)
                filtered_df = df[df['State'].isin(selected_states)]
            else:
                filtered_df = df

            numeric_cols = df.select_dtypes(include='number').columns.tolist()

            if numeric_cols and not df.empty:
                col_to_filter = st.selectbox("Select numeric column to filter", numeric_cols)

                if col_to_filter in ['Sales Amt', 'Qty']:
                    threshold = st.slider(
                        f"Select minimum value for {col_to_filter}",
                        int(df[col_to_filter].min()),
                        int(df[col_to_filter].max())
                    )
                    filtered_df = filtered_df[filtered_df[col_to_filter] > threshold]
                else:
                    unique_vals = sorted(df[col_to_filter].dropna().unique())
                    selected_vals = st.multiselect(
                        f"Select values to filter for {col_to_filter}",
                        options=unique_vals,
                        default=unique_vals
                    )
                    filtered_df = filtered_df[filtered_df[col_to_filter].isin(selected_vals)]

                st.session_state.merged_df = filtered_df
                st.write(f"Filtered Data", filtered_df.head(1000))

                # Download button
                st.download_button("Download Filtered CSV", filtered_df.to_csv(index=False), file_name="filtered_primary_data.csv", mime='text/csv')

            else:
                st.warning("No numeric columns found or no data available after filtering.")            
    else:
        st.info("Upload the primary CSV file to start the pipeline.")

# EXCEPTIONS TAB
with tab2:
    # Check if merged_df is available before calling the exceptions logic
    if "merged_df" in st.session_state and st.session_state.merged_df is not None:
        show_exceptions_tab(st.session_state.merged_df)
    else:
        st.warning("⚠️ Please complete the ETL pipeline first to run exception checks.")


with tab3:
    show_reports_tab(st.session_state.get("merged_df"))
   

with tab4:
    show_forecast_tab(st.session_state.get("merged_df"))

with tab5:
    show_faq_tab()

       
