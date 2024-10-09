import pandas as pd
from transformers import pipeline
import re  # Import the re module

################################
### INITIALIZATION FUNCTIONS ###
################################

# Fungsi untuk memuat data dari file excel yang sudah tersedia
def load_data_pht():
    df_pht = pd.read_excel('DataPHT.xlsx')
    df_mitigasi = pd.read_excel('500kV Transmission Line Contingencies_Updated.xlsx', sheet_name='Contingency')
    df_pembangkitan = pd.read_excel('Data_Pembangkit.xlsx')
    return df_pht, df_mitigasi, df_pembangkitan

# Inisialisasi pipeline dari Hugging Face Transformers untuk pertanyaan-jawaban (Q&A)
qa_model = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")

#####################
### PHT FUNCTIONS ###
#####################

# Fungsi untuk mencari data berdasarkan kata kunci, tidak peka terhadap huruf besar/kecil
def search_data(df, keyword):
    # Convert semua kolom dan baris ke huruf kecil untuk pencarian case-insensitive
    df_lower = df.applymap(lambda s: s.lower() if isinstance(s, str) else s)
    keyword_lower = keyword.lower()  # Konversi keyword menjadi huruf kecil
    
    # Cari data yang mengandung kata kunci di salah satu kolom
    result = df_lower[df_lower.apply(lambda row: row.astype(str).str.contains(keyword_lower).any(), axis=1)]
    
    if result.empty:
        return None
    else:
        return result

# Fungsi untuk membangun konteks dari data dan menyusun respons deskriptif
def build_context_and_response(df, keyword):
    # Cari data berdasarkan kata kunci (case-insensitive)
    result = search_data(df, keyword)
    
    if result is None:
        return None, "Data tidak ditemukan untuk kata kunci yang diminta."
    else:
        # Convert the keyword to highlighted text using a span tag with background color
        keyword_highlighted = f'<span style="background-color: yellow">{keyword.upper()}</span>'
        
        # Menyusun kalimat deskriptif untuk setiap baris yang ditemukan
        responses = []
        for index, row in result.iterrows():
            dari_gitet = row['Dari Gitet/Gistet'].upper()
            ke_gitet = row['Ke Gitet/Gistet'].upper()
            Sirkit = row['Sirkit ke']
            panjang = row['Panjang Penghantar'] if not pd.isnull(row['Panjang Penghantar']) else 'tidak tersedia'
            nominal = row['Nominal Arus (A)'] if not pd.isnull(row['Nominal Arus (A)']) else 'tidak tersedia'
            kemampuan_max = row['Kemampuan Penghantar (A)'] if not pd.isnull(row['Kemampuan Penghantar (A)']) else 'tidak tersedia'
            wilayah = row['Wilayah'].upper() if not pd.isnull(row['Wilayah']) else 'tidak tersedia'
            derating = row['Keterangan Penyebab Derating'] if not pd.isnull(row['Keterangan Penyebab Derating']) else 'tidak tersedia'
            persen_derating = row['Deklarasi Kemampuan (%)']*100 if not pd.isnull(row['Deklarasi Kemampuan (%)']) else 'tidak tersedia'
                
            # Buat kalimat deskriptif
            description = (f"SUTET {dari_gitet}-{ke_gitet} #{Sirkit} ada di wilayah {wilayah} "
                           f"dengan panjang penghantar {panjang} km dan kemampuan maksimal sebesar "
                           f"{kemampuan_max} A, {persen_derating} % dari nominal {nominal} A. Alasan Derating: {derating}.")
            
            # Replace the keyword in the response with the highlighted version, using re.sub for case-insensitive replacement
            description = re.sub(keyword, keyword_highlighted, description, flags=re.IGNORECASE)
            
            responses.append(description)
        
        # Tambahkan nomor pada setiap respons
        full_response = "\n".join(f"{i + 1}. {resp}" for i, resp in enumerate(responses))
        context = result.to_string(index=False)
        return context, full_response

##########################
### MITIGASI FUNCTIONS ###
##########################

def search_data_mitigasi(df_1, keyword):
    # Convert semua kolom dan baris ke huruf kecil untuk pencarian case-insensitive
    df_lower_ = df_1.applymap(lambda s: s.upper() if isinstance(s, str) else s)
    keyword_lower = keyword.upper()  # Konversi keyword menjadi huruf besar
    
    # Cari data yang mengandung kata kunci di salah satu kolom
    result = df_lower_[df_lower_.apply(lambda row: row.astype(str).str.contains(keyword_lower).any(), axis=1)]
    
    if result.empty:
        return None
    else:
        return result

# MITIGASI
def build_context_and_response_mitigasi(df_1, keyword):
    result = search_data_mitigasi(df_1, keyword)
    
    if result is None:
        return None, "Data tidak ditemukan untuk kata kunci yang diminta."
    else:
        # Convert the keyword to highlighted text using a span tag with background color
        keyword_highlighted = f'<span style="background-color: yellow">{keyword.upper()}</span>'
        
        # Menyusun kalimat deskriptif untuk setiap baris yang ditemukan
        responses_mitigasi = []
        for index, row in result.iterrows():
            SUTET = row.get('SUTET', 'SUTET tidak ditemukan')
            N_1 = row.get('N-1', 'Data N-1 tidak ditemukan')
            Mit_1 = row.get('Mitigasi_1', 'tidak tersedia')
            N_1_1 = row.get('N-1-1', 'tidak tersedia')
            Mit_2 = row.get('Mitigasi_2', 'tidak tersedia')
            N_1_2 = row.get('N-1-2', 'tidak tersedia')
            Mit_3 = row.get('Mitigasi_3', 'tidak tersedia')
            Ket = row.get('Ket', 'tidak ada')

            # Helper function to format mitigation steps and handle NaN values
            def format_mitigation(mitigation):
                if pd.isna(mitigation):
                    return "Tidak ada mitigasi yang tersedia."
                # Split each line, and add a "-" before each line to make it a bullet point.
                lines = mitigation.splitlines()
                formatted_lines = "\n".join([f"- {line.strip()}" for line in lines if line.strip()])
                return formatted_lines

            # Buat kalimat deskriptif
            description = (f"## ***{SUTET}***\n\n"
                        f"Jika terjadi gangguan di ruas **{SUTET}**, mitigasi yang harus dilakukan adalah sebagai berikut:\n\n"
                        f"**MITIGASI N-1** di ruas **{N_1}**:\n{format_mitigation(Mit_1)}\n\n"
                        f"**MITIGASI N-1-1** di ruas **{N_1_1}**:\n{format_mitigation(Mit_2)}\n\n"
                        f"**MITIGASI N-1-2** di ruas **{N_1_2}**:\n{format_mitigation(Mit_3)}\n\n"
                        f"**KETERANGAN** : **{Ket}**")

            # Replace the keyword in the response with the highlighted version, using re.sub for case-insensitive replacement
            description = re.sub(keyword, keyword_highlighted, description, flags=re.IGNORECASE)

            # Append the description to the list
            responses_mitigasi.append(description)

        # Combine all responses into one formatted string
        full_response = "\n\n".join(responses_mitigasi)  # Use double newline for clarity between entries

        # Convert the context (dataframe) to a string without row indices
        context = result.to_string(index=False)

        return context, full_response
    
##############################
### PEMBANGKITAN FUNCTIONS ###
##############################

def search_data_pembangkitan(df_2, keyword):
    # Convert semua kolom dan baris ke huruf besar untuk pencarian case-insensitive
    df_lower_ = df_2.applymap(lambda s: s.upper() if isinstance(s, str) else s)
    keyword_upper = keyword.upper()  # Konversi keyword menjadi huruf besar

    # Cari data yang mengandung kata kunci di salah satu kolom
    result = df_lower_[df_lower_.apply(lambda row: row.astype(str).str.contains(keyword_upper).any(), axis=1)]
    
    if result.empty:
        return None
    else:
        return result

# Function to dynamically build the context and response in table format, now supporting 'Unit', 'Jenis Pembangkit', and 'Perusahaan'
def build_context_and_response_pembangkitan(df_2, keyword):
    # Ensure DMN and TML are numeric, replace any non-numeric values with 0
    df_2['DMN'] = pd.to_numeric(df_2['DMN'], errors='coerce').fillna(0)
    df_2['TML'] = pd.to_numeric(df_2['TML'], errors='coerce').fillna(0)

    # Search the data based on the keyword (both 'Perusahaan', 'Wilayah', 'Jenis Pembangkit', and 'Unit')
    result = search_data_pembangkitan(df_2, keyword)

    if result is None:
        return None, "Data tidak ditemukan untuk kata kunci yang diminta."
    else:
        # Check if the keyword matches 'Perusahaan', 'Wilayah', 'Jenis', or 'Unit'
        perusahaan_matches = result['Perusahaan'].str.contains(keyword, case=False, na=False)
        jenis_matches = result['Jenis'].str.contains(keyword, case=False, na=False)
        unit_matches = result['Unit '].str.contains(keyword, case=False, na=False)

        if perusahaan_matches.any():
            # Extract the first matching 'Perusahaan' for the title
            perusahaan_title = result.loc[perusahaan_matches, 'Perusahaan'].iloc[0]  # Get the first matching Perusahaan

            # Group the result by 'Wilayah' and show the sum of 'DMN' and 'TML' for each 'Wilayah'
            grouped = result.groupby('Wilayah').agg({
                'DMN': 'sum',
                'TML': 'sum'
            }).reset_index()

            # Create a DataFrame for display and highlight the keyword
            def highlight_keyword(text, keyword):
                return re.sub(f"({keyword})", r"<span style='background-color: yellow'>\1</span>", text, flags=re.IGNORECASE)

            highlighted_df = result.applymap(lambda x: highlight_keyword(str(x), keyword) if isinstance(x, str) else x)

            # Build tables for each Wilayah with sum of DMN and TML at the bottom
            wilayahs = highlighted_df['Wilayah'].unique()
            full_html = ""

            # Iterate over each Wilayah, display data, and include sum at the bottom
            for wilayah in wilayahs:
                wilayah_data = highlighted_df[highlighted_df['Wilayah'] == wilayah]
                wilayah_dmn_sum = wilayah_data['DMN'].sum()
                wilayah_tml_sum = wilayah_data['TML'].sum()

                # Convert wilayah data to HTML table
                table_html = wilayah_data[['Perusahaan', 'Jenis', 'Unit ', 'DMN', 'TML']].to_html(escape=False, index=False)

                # Append the sum of DMN and TML at the bottom of each Wilayah's table
                sum_html = f"<tr><td><strong>Total for {wilayah}</strong></td><td></td><td><strong>{round(wilayah_dmn_sum, 2)}</strong></td><td><strong>{round(wilayah_tml_sum, 2)}</strong></td></tr>"

                # Wrap in HTML for each Wilayah and combine
                full_html += f"<h3>Wilayah: {wilayah}</h3>{table_html}<table>{sum_html}</table><br><br>"

            # Add the global sum of DMN and TML for all Wilayah at the bottom
            global_dmn_sum = round(result['DMN'].sum(), 2)  # Round to 2 decimal places
            global_tml_sum = round(result['TML'].sum(), 2)  # Round to 2 decimal places
            global_sum_html = f"<h3>Global Sum</h3><table><tr><td><strong>Total DMN (MW):</strong></td><td><strong>{global_dmn_sum}</strong></td></tr><tr><td><strong>Total TML (MW):</strong></td><td><strong>{global_tml_sum}</strong></td></tr></table>"

            # Combine everything into the final HTML output
            full_html += global_sum_html

            # Include Perusahaan in the title
            return f"Perusahaan: {perusahaan_title.upper()}", full_html

        # Check if the keyword matches 'Jenis Pembangkit'
        elif jenis_matches.any():
            # Filter data for the specific Jenis Pembangkit (Type of Power Plant)
            jenis_data = result[result['Jenis'].str.contains(keyword, case=False)]

            # Separate data into each 'Wilayah'
            wilayahs = jenis_data['Wilayah'].unique()
            full_html = ""

            # Iterate over each Wilayah and create separate tables
            for wilayah in wilayahs:
                wilayah_data = jenis_data[jenis_data['Wilayah'] == wilayah]
                wilayah_dmn_sum = wilayah_data['DMN'].sum()
                wilayah_tml_sum = wilayah_data['TML'].sum()

                # Highlight the keyword in the table
                def highlight_keyword(text, keyword):
                    return re.sub(f"({keyword})", r"<span style='background-color: yellow'>\1</span>", text, flags=re.IGNORECASE)

                highlighted_df = wilayah_data.applymap(lambda x: highlight_keyword(str(x), keyword) if isinstance(x, str) else x)

                # Convert data to HTML table and add sum at the bottom
                table_html = highlighted_df[['Perusahaan', 'Jenis', 'Unit ', 'DMN', 'TML']].to_html(escape=False, index=False)
                sum_html = f"<tr><td><strong>Total for {wilayah}</strong></td><td></td><td><strong>{round(wilayah_dmn_sum, 2)}</strong></td><td><strong>{round(wilayah_tml_sum, 2)}</strong></td></tr>"

                # Wrap in HTML for each Wilayah and combine
                full_html += f"<h3>Wilayah: {wilayah}</h3>{table_html}<table>{sum_html}</table><br><br>"

            # Add the global sum of DMN and TML for all Wilayah at the bottom
            global_dmn_sum = round(jenis_data['DMN'].sum(), 2)  # Round to 2 decimal places
            global_tml_sum = round(jenis_data['TML'].sum(), 2)  # Round to 2 decimal places
            global_sum_html = f"<h3>Global Sum</h3><table><tr><td><strong>Total DMN (MW):</strong></td><td><strong>{global_dmn_sum}</strong></td></tr><tr><td><strong>Total TML (MW):</strong></td><td><strong>{global_tml_sum}</strong></td></tr></table>"

            # Combine everything into the final HTML output
            final_html = f"<h3>Jenis Pembangkit: {keyword.upper()}</h3>{full_html}{global_sum_html}"

            return f"Jenis Pembangkit: {keyword.upper()}", final_html

        # Check if the keyword matches 'Unit'
        elif unit_matches.any():
            # Filter data for the specific Unit
            unit_data = result[result['Unit '].str.contains(keyword, case=False)]

            # Separate data into each 'Wilayah'
            wilayahs = unit_data['Wilayah'].unique()
            full_html = ""

            # Iterate over each Wilayah and create separate tables
            for wilayah in wilayahs:
                wilayah_data = unit_data[unit_data['Wilayah'] == wilayah]
                wilayah_dmn_sum = wilayah_data['DMN'].sum()
                wilayah_tml_sum = wilayah_data['TML'].sum()

                # Highlight the keyword in the table
                def highlight_keyword(text, keyword):
                    return re.sub(f"({keyword})", r"<span style='background-color: yellow'>\1</span>", text, flags=re.IGNORECASE)

                highlighted_df = wilayah_data.applymap(lambda x: highlight_keyword(str(x), keyword) if isinstance(x, str) else x)

                # Convert data to HTML table and add sum at the bottom
                table_html = highlighted_df[['Perusahaan', 'Jenis', 'Unit ', 'DMN', 'TML']].to_html(escape=False, index=False)
                sum_html = f"<tr><td><strong>Total for {wilayah}</strong></td><td></td><td><strong>{round(wilayah_dmn_sum, 2)}</strong></td><td><strong>{round(wilayah_tml_sum, 2)}</strong></td></tr>"

                # Wrap in HTML for each Wilayah and combine
                full_html += f"<h3>Wilayah: {wilayah}</h3>{table_html}<table>{sum_html}</table><br><br>"

            # Add the global sum of DMN and TML for all Wilayah at the bottom
            global_dmn_sum = round(unit_data['DMN'].sum(), 2)  # Round to 2 decimal places
            global_tml_sum = round(unit_data['TML'].sum(), 2)  # Round to 2 decimal places
            global_sum_html = f"<h3>Global Sum</h3><table><tr><td><strong>Total DMN (MW):</strong></td><td><strong>{global_dmn_sum}</strong></td></tr><tr><td><strong>Total TML (MW):</strong></td><td><strong>{global_tml_sum}</strong></td></tr></table>"

            # Combine everything into the final HTML output
            final_html = f"<h3>Unit: {keyword.upper()}</h3>{full_html}{global_sum_html}"

            return f"Unit: {keyword.upper()}", final_html

        # If the keyword matches in 'Wilayah'
        elif any(df_2['Wilayah'].str.contains(keyword, case=False, na=False)):
            # Filter data for the specific Wilayah
            wilayah_data = result[result['Wilayah'].str.contains(keyword, case=False)]

            # Sum the DMN and TML for the selected Wilayah
            wilayah_dmn_sum = wilayah_data['DMN'].sum()
            wilayah_tml_sum = wilayah_data['TML'].sum()

            # Highlight the keyword in the table
            def highlight_keyword(text, keyword):
                return re.sub(f"({keyword})", r"<span style='background-color: yellow'>\1</span>", text, flags=re.IGNORECASE)

            highlighted_df = wilayah_data.applymap(lambda x: highlight_keyword(str(x), keyword) if isinstance(x, str) else x)

            # Convert data to HTML table and add sum at the bottom
            table_html = highlighted_df[['Perusahaan', 'Jenis', 'Unit ', 'DMN', 'TML']].to_html(escape=False, index=False)
            sum_html = f"<tr><td><strong>Total for {keyword.upper()}</strong></td><td></td><td><strong>{round(wilayah_dmn_sum, 2)}</strong></td><td><strong>{round(wilayah_tml_sum, 2)}</strong></td></tr>"

            # Add the global sum of DMN and TML for the entire dataset
            global_dmn_sum = round(result['DMN'].sum(), 2)  # Round to 2 decimal places
            global_tml_sum = round(result['TML'].sum(), 2)  # Round to 2 decimal places
            global_sum_html = f"<h3>Global Sum</h3><table><tr><td><strong>Total DMN (MW):</strong></td><td><strong>{global_dmn_sum}</strong></td></tr><tr><td><strong>Total TML (MW):</strong></td><td><strong>{global_tml_sum}</strong></td></tr></table>"

            # Combine everything into the final HTML output
            final_html = f"<h3>Wilayah: {keyword.upper()}</h3>{table_html}<table>{sum_html}</table><br><br>{global_sum_html}"

            return f"Wilayah: {keyword.upper()}", final_html

        else:
            return None, "Data tidak ditemukan untuk kata kunci yang diminta."





###########################
### ANSWERING FUNCTIONS ###
###########################

# Fungsi untuk mendapatkan jawaban dari model QA
def get_answer(question, context):
    # Pastikan konteks tersedia
    if context:
        result = qa_model(question=question, context=context)
        return result['answer']
    else:
        return "Data tidak ditemukan untuk kata kunci yang diminta."
