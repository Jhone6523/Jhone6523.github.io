from fastapi import FastAPI, HTTPException, Request
import os
from github import Github
import requests
from PIL import Image, ImageDraw, ImageFont
import glob
import feedparser
import io
from boto.s3.connection import S3Connection
from pydantic import BaseModel

app = FastAPI()

class UploadRequest(BaseModel):
    # Déclarez les données attendues dans le corps de la requête
    image_url: str
    auteur: str
    via: str
    caption: str

@app.post("/")
def upload_and_publish(data: UploadRequest, request: Request):
    try:
        cookie_del = glob.glob("config/*cookie.json")

        if cookie_del:
            if os.path.exists(cookie_del[0]):
                os.remove(cookie_del[0])

        chemin_de_l_image = "credited_image.jpg.REMOVE_ME"

        # Vérifiez si le fichier image existe
        if os.path.exists(chemin_de_l_image):
            # Supprimez le fichier image
            os.remove(chemin_de_l_image)
            print(f"L'image {chemin_de_l_image} a été supprimée avec succès.")
        else:
            print(f"L'image {chemin_de_l_image} n'existe pas.")

        rss_url = "https://www.futura-sciences.com/rss/actualites.xml"

        feed = feedparser.parse(rss_url)

        for entry in feed.entries:
            print("Title:", entry.title)
            print("Link:", entry.link)
            print("Published Date:", entry.published)
            print("Summary:", entry.summary)
            print("\n")

            # Lien de l'image que vous voulez télécharger
        url = data.image_url

        # Envoyer une requête GET pour obtenir le contenu de l'image
        response = requests.get(url)

        # Vérifier si la requête a réussi (statut 200 OK)
        if response.status_code == 200:
            # Obtenir le contenu de l'image
            image_content = response.content

            # Spécifier le nom du fichier dans lequel vous voulez enregistrer l'image
            nom_fichier = "phoque.jpg"

            # Écrire le contenu de l'image dans le fichier
            with open(nom_fichier, "wb") as fichier:
                fichier.write(image_content)
            
            print(f"L'image a été téléchargée et enregistrée sous le nom '{nom_fichier}'.")

        else:
            print("Échec du téléchargement de l'image. Statut de la requête :", response.status_code)

        # Ouvrez l'image
        image = Image.open(nom_fichier)

        largeur, hauteur = image.size
        
        taille_cote = min(largeur, hauteur)
        left = (largeur - taille_cote) / 2
        top = (hauteur - taille_cote) / 2
        right = (largeur + taille_cote) / 2
        bottom = (hauteur + taille_cote) / 2
        
        # Recadrer l'image pour en faire un carré de 800x800
        image_cropee = image.crop((left, top, right, bottom))
        
        image = image_cropee.resize((800, 800),Image.LANCZOS)
        # Créez un contexte de dessin
        draw = ImageDraw.Draw(image)

        largeur, hauteur = image.size


        # Définissez les coordonnées du point de départ et de fin du bandeau rouge
        point_depart = (0, hauteur - (hauteur // 1.5))  # Le point de départ est au milieu de l'image en bas
        point_fin = (largeur, hauteur)  # Le point de fin est au coin inférieur droit de l'image

        # Dessinez le rectangle rouge
        couleur_bandeau = (255, 255, 255)  # Blanc (R, G, B)
        draw.rectangle([point_depart, point_fin], fill=couleur_bandeau)

        # Dessinez les contours blancs autour du rectangle rouge
        couleur_contours = (178,34,34)  # Rouge (R, G, B)
        largeur_bordure = 40
        position_ligne = (point_depart[0], point_fin[1])  # Point de départ de la ligne
        longueur_ligne = largeur  # La ligne s'étend sur toute la largeur de l'image
        draw.line([position_ligne, (position_ligne[0] + longueur_ligne, position_ligne[1])], fill=couleur_contours, width=largeur_bordure)


        # Spécifiez la police, le texte et la couleur du texte
        font_mentions = ImageFont.truetype("arial.ttf", 14)  # Utilisez la police Arial avec la taille appropriée
        mentions_text = "Photo par " + data.auteur + " \n Via " + data.via  # Texte des mentions
        mentions_text_color = (255, 255, 255)  # Couleur blanche (R, G, B)
        
        # Spécifiez la couleur du contour pour les mentions
        mentions_outline_color = (0, 0, 0)  # Couleur du contour (noir)
        mentions_outline_width = 2  # Largeur du contour
        
        



        # Calculez la largeur du texte en utilisant textbbox
        textbbox = draw.textbbox((0, 0), mentions_text, font=font_mentions)

        # Calcul de la largeur du texte
        text_width = textbbox[2] - textbbox[0]

        # Positionnez le texte dans le coin supérieur droit de l'image sans dépasser les limites
        max_x = image.width - text_width - 10  # 10 pixels de marge depuis le bord droit
        max_y = 10  # 10 pixels de marge depuis le bord supérieur

        # Assurez-vous que le texte ne dépasse pas les limites de l'image
        x = min(max_x, max(10, max_x))  # Assurez-vous que x est dans la plage [10, max_x]

        # Dessiner les mentions "Photo de" et "Via" avec contour noir
        for dx in [-mentions_outline_width, 0, mentions_outline_width]:
            for dy in [-mentions_outline_width, 0, mentions_outline_width]:
                draw.text((x + dx, max_y + dy), mentions_text, fill=mentions_outline_color, font=font_mentions)
                
        # Ajoutez le texte de crédit à l'image
        draw.text((x, max_y), mentions_text, fill=mentions_text_color, font=font_mentions)



        # Spécifiez la police, le texte et la couleur du texte
        font_size = 32
        font = ImageFont.truetype("arial.ttf", font_size)  # Utilisez la police Arial avec une taille initiale

        text = data.caption
        text_color = (0, 0, 0)  # Couleur du texte (R, G, B)

        # Calculez la hauteur maximale pour le texte (pour qu'il n'y ait pas de débordement)
        max_text_height = point_fin[1] - point_depart[1]

        # Calculez la largeur du texte avec la police actuelle
        textbbox = draw.textbbox((0, 0), text, font=font)
        text_width = textbbox[2] - textbbox[0]

        # Fonction pour ajouter automatiquement des retours à la ligne en cas de débordement et centrer le texte
        def wrap_and_center_text(text, font, max_width):
            lines = []
            current_line = []
            current_line_width = 0

            for word in text.split():
                word_bbox = draw.textbbox((0, 0), word, font=font)
                word_width = word_bbox[2] - word_bbox[0]

                if current_line_width + word_width <= max_width:
                    current_line.append(word)
                    current_line_width += word_width + draw.textbbox((0, 0), " ", font=font)[2] - draw.textbbox((0, 0), " ", font=font)[0]
                else:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_line_width = word_width + draw.textbbox((0, 0), " ", font=font)[2] - draw.textbbox((0, 0), " ", font=font)[0]

            if current_line:
                lines.append(" ".join(current_line))

            # Centrer le texte en fonction de la largeur maximale
            centered_lines = []
            for line in lines:
                line_bbox = draw.textbbox((0, 0), line, font=font)
                line_width = line_bbox[2] - line_bbox[0]
                centered_x = (max_width - line_width) / 2
                centered_lines.append((line, centered_x))

            return centered_lines

        # Ajoutez le texte en tenant compte de la hauteur maximale
        wrapped_and_centered_lines = wrap_and_center_text(text, font, largeur)

        # Dessinez le texte en tenant compte de la hauteur maximale
        current_y = point_depart[1] + 10 # Position y (en bas du rectangle)
        for line, centered_x in wrapped_and_centered_lines:
            textbbox = draw.textbbox((0, 0), line, font=font)
            text_height = textbbox[3] - textbbox[1]

            if current_y + text_height <= point_fin[1]:
                # Si le texte tient dans la hauteur maximale, ajoutez-le
                x = centered_x  # Position x (centrée par rapport au rectangle)
                y = current_y  # Position y (en bas du rectangle)
                draw.text((x, y), line, fill=text_color, font=font)
                current_y += text_height  # Met à jour la position y pour le texte suivant



        # Enregistrez l'image modifiée
        modified_image_path = 'credited_image.jpg'
        # Get the base URL of the current request
        current_domain = str(request.base_url)

        # Return the URL of the modified image
        modified_image_url = f"{current_domain}{modified_image_path}"

        
        # Remplacez ces valeurs par vos informations d'authentification GitHub
        nom_utilisateur = "Jhone6523"
        mot_de_passe = os.environ['S3_API']

        # Créez une instance de l'objet GitHub
        github = Github(nom_utilisateur, mot_de_passe)

        # Récupérez le dépôt (repository) dans lequel vous avez ajouté le fichier
        nom_depot = "imageinsta"
        depot = github.get_user().get_repo(nom_depot)

        # Spécifiez le chemin et le nom du fichier que vous avez ajouté
        chemin_fichier = "image.jpg"

        # Spécifiez le contenu que vous avez mis dans le fichier (peut être vide)
        contenu_fichier = "Contenu de votre fichier."
        
        # Enregistrez l'image modifiée en tant qu'octets (bytes)
        output_image = io.BytesIO()
        image.save(output_image, format="JPEG")  # Assurez-vous de spécifier le format approprié

        # Rembobinez le flux d'octets pour le lire à partir du début
        output_image.seek(0)
        fichier = depot.get_contents(chemin_fichier)
        nouveau_contenu = output_image.read()
        # Créez le fichier dans le dépôt
        depot.update_file(
            chemin_fichier,
            "Message de commit pour la mise à jour du fichier",
            nouveau_contenu,
            fichier.sha,  # SHA actuel du fichier, nécessaire pour la mise à jour
            branch="master"  # Branche dans laquelle vous souhaitez effectuer la mise à jour
        )

        # Construisez l'URL de téléchargement direct
        lien_fichier = f"https://github.com/Jhone6523/imageinsta/blob/master/image.jpg?raw=true"

        print(f'Le fichier "{chemin_fichier}" a été ajouté avec succès au dépôt GitHub "{nom_depot}".')
        print(f'Le lien vers le fichier est : {lien_fichier}')


        return {'message': 'Image publiée avec succès','lien': lien_fichier}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
