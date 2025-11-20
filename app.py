import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

# ==========================================
# 1. CONFIGURAZIONE PAGINA
# ==========================================
st.set_page_config(page_title="D&D Scheduler", page_icon="🎲", layout="wide")

st.title("🎲 D&D Party Scheduler")
st.markdown("Inserisci la tua disponibilità. **0.0** = No, **0.5** = Posso Organizzarmi, **1.0** = Slot Preferito")

# ==========================================
# 2. GESTIONE DATI (Database CSV simulato)
# ==========================================
FILE_DATA = 'disponibilita.csv'
MASTER_NAME = 'Fado'
PLAYERS = ['Sore', 'Eva', 'Drugo', 'PG', 'Gio', 'Gian', 'Fado']
SLOTS = [
    'Lun Sera', 'Mar Sera', 'Mer Sera', 'Gio Sera', 'Ven Sera', 
    'Sab Matt', 'Sab Pom', 'Dom Matt', 'Dom Pom'
]

# Se il file non esiste, creiamo un template vuoto
if not os.path.exists(FILE_DATA):
    default_data = {p: [0.0]*len(SLOTS) for p in PLAYERS}
    default_data['Slot'] = SLOTS
    df_init = pd.DataFrame(default_data).set_index('Slot')
    df_init.to_csv(FILE_DATA)

# Carichiamo i dati attuali
df = pd.read_csv(FILE_DATA, index_col='Slot')

# ==========================================
# 3. INTERFACCIA UTENTE (INPUT)
# ==========================================
with st.sidebar:
    st.header("👤 Chi sei?")
    user = st.selectbox("Seleziona il tuo nome", PLAYERS)
    
    st.warning(f"Stai modificando per: **{user}**")
    
    # Form per l'input
    with st.form("my_form"):
        st.write("Le tue disponibilità:")
        new_values = []
        for slot in SLOTS:
            # Prendi il valore attuale
            current_val = float(df.loc[slot, user])
            # Slider per 0, 0.5, 1
            val = st.select_slider(
                label=slot, 
                options=[0.0, 0.5, 1.0], 
                value=current_val,
                format_func=lambda x: "❌ No" if x==0 else ("⚠️ Forse" if x==0.5 else "✅ Sì")
            )
            new_values.append(val)
        
        submitted = st.form_submit_button("💾 Salva Disponibilità")
        
        if submitted:
            df[user] = new_values
            df.to_csv(FILE_DATA)
            st.success("Salvato! Ricarica la pagina se non vedi i grafici aggiornati.")

# ==========================================
# 4. LOGICA DI CALCOLO (Il tuo algoritmo)
# ==========================================
QUORUM = 4

def calculate_score(row):
    master_w = row[MASTER_NAME]
    # Somma gli altri escluso il master
    others = row.drop(MASTER_NAME).sum()
    # Logica: Se master è 0, tutto 0. Se Master c'è, somma + master.
    return master_w * (others + 1)

# Calcolo punteggi live
df_calc = df.copy()
df_calc['Score'] = df_calc.apply(calculate_score, axis=1)

best_slot = df_calc['Score'].idxmax()
best_score = df_calc['Score'].max()

# ==========================================
# 5. DASHBOARD GRAFICA
# ==========================================
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 Mappa Termica del Party")
    # Heatmap
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    sns.heatmap(df, annot=True, cmap="RdYlGn", vmin=0, vmax=1, cbar=False, linewidths=.5, ax=ax1)
    st.pyplot(fig1)

with col2:
    st.subheader("🏆 Classifica Slot")
    # Bar Chart
    fig2, ax2 = plt.subplots(figsize=(5, 6))
    colors = ['grey' if s < QUORUM else 'green' for s in df_calc['Score']]
    ax2.bar(df_calc.index, df_calc['Score'], color=colors)
    ax2.axhline(y=QUORUM, color='r', linestyle='--', label='Quorum')
    plt.xticks(rotation=45)
    st.pyplot(fig2)

# KPI
st.divider()
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Miglior Giorno", best_slot)
kpi1.metric("Score", f"{best_score:.1f}")

status_master = "✅ Presente" if df.loc[best_slot, MASTER_NAME] > 0 else "❌ ASSENTE"
kpi2.metric("Stato Master", status_master)

# Chi manca nel giorno migliore?
assenti = []
for p in PLAYERS:
    if df.loc[best_slot, p] == 0:
        assenti.append(p)

kpi3.write(f"**Assenti nel giorno migliore:** {', '.join(assenti) if assenti else 'Nessuno!'}")
