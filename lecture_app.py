import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import openai
import json

# ---------------------- CONFIG ----------------------
st.set_page_config(page_title="Mes Articles", layout="wide")

# Init DB (simple JSON stored in session_state)
if "articles" not in st.session_state:
    st.session_state.articles = []  # each article: {url, title, length, summary}

# ---------------------- FUNCTIONS ----------------------

def fetch_article_metadata(url: str):
    """Extract the title and length (word count) of an article."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Title extraction
        title = soup.title.string if soup.title else "Sans titre"

        # Approximate text length
        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text() for p in paragraphs])
        length = len(text.split())

        return title, length, text
    except Exception:
        return None, None, None


def generate_summary(text: str, max_chars: int = 6000):
    """Call OpenAI API to summarize the article."""
    try:
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        prompt = f"Résume ce texte en moins de {max_chars} signes :\n{text}"

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"Erreur API : {e}"


# ---------------------- UI ----------------------
st.title("📰 Gestionnaire d'Articles & Résumés IA")
st.write("Centralisez vos articles, gardez-les pour plus tard et générez des résumés instantanés.")

# Add article
st.subheader("Ajouter un article")
new_url = st.text_input("URL de l'article (optionnel)")
man_text = st.text_area("Ou collez directement le texte de l'article :", height=200)

if st.button("Ajouter"):
    if not new_url and not man_text:
        st.error("Veuillez entrer une URL ou coller un texte.")
    else:
        if man_text:
            title = "Article collé manuellement"
            length = len(man_text.split())
            text = man_text
        else:
            title, length, text = fetch_article_metadata(new_url)
            if not title:
                st.error("Impossible d'extraire l'article. URL valide ?")
            
        if text:
            st.session_state.articles.append({
                "url": new_url if new_url else "(texte collé)",
                "title": title,
                "length": length,
                "content": text,
                "summary": None
            })
            st.success(f"Article ajouté : {title}")

# List articles
st.subheader("Vos articles enregistrés")

if not st.session_state.articles:
    st.info("Aucun article enregistré pour le moment.")
else:
    for idx, article in enumerate(st.session_state.articles):
        with st.container():
            st.markdown(f"### {article['title']}")
            st.write(f"📏 Longueur : {article['length']} mots")
            st.write(f"🔗 [Lien vers l'article]({article['url']})")

            col1, col2, col3 = st.columns([1,1,1])

            # Generate summary
            with col1:
                if st.button("Résumé IA", key=f"summary_{idx}"):
                    with st.spinner("Génération du résumé..."):
                        summary = generate_summary(article["content"])
                        st.session_state.articles[idx]["summary"] = summary
                        st.success("Résumé généré ! Faites défiler pour le voir.")

            # Delete article
            with col2:
                if st.button("Supprimer", key=f"delete_{idx}"):
                    st.session_state.articles.pop(idx)
                    st.rerun()

            # Show summary
            if article.get("summary"):
                st.markdown("#### Résumé IA ✨")
                st.write(article["summary"])

st.write("---")
st.caption("Application Streamlit minimale avec résumé IA.")
