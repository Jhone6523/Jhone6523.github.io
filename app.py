from fastapi import FastAPI, HTTPException, Request
import os
from fastapi.responses import FileResponse, HTMLResponse
import requests
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel
import uvicorn
from fastapi import FastAPI
from uvicorn.config import Config
import uuid
from fastapi.templating import Jinja2Templates
from fastapi import Request
import json
import datetime

app = FastAPI()
if __name__ == "__main__":

    config = Config(app=app, host="0.0.0.0", port=49966)


    server = uvicorn.Server(config)


    port_used = server.config.port

    print(f"FastAPI est en cours d'exécution sur le port {port_used}")


    server.run()
class UploadRequest(BaseModel):

    image_url: str
    auteur: str
    via: str
    headline: str
    caption : str

@app.post("/")
def upload_and_publish(data: UploadRequest, request: Request):
    try:


        url = data.image_url

        response = requests.get(url)

        if response.status_code == 200:

            image_content = response.content

            nom_fichier = "phoque.jpg"

            with open(nom_fichier, "wb") as fichier:
                fichier.write(image_content)
            
            print(f"L'image a été téléchargée et enregistrée sous le nom '{nom_fichier}'.")

        else:
            print("Échec du téléchargement de l'image. Statut de la requête :", response.status_code)

        image = Image.open(nom_fichier)

        largeur, hauteur = image.size
        
        taille_cote = min(largeur, hauteur)
        left = (largeur - taille_cote) / 2
        top = (hauteur - taille_cote) / 2
        right = (largeur + taille_cote) / 2
        bottom = (hauteur + taille_cote) / 2
        
        image_cropee = image.crop((left, top, right, bottom))
        
        image = image_cropee.resize((800, 800),Image.LANCZOS)
        draw = ImageDraw.Draw(image)

        largeur, hauteur = image.size


        point_depart = (0, hauteur // 1.5)  
        point_fin = (largeur, hauteur)  


        couleur_bandeau = (255, 255, 255)  
        draw.rectangle([point_depart, point_fin], fill=couleur_bandeau)

        
        couleur_contours = (197,68,62)  
        largeur_bordure = 40
        position_ligne = (point_depart[0], point_fin[1])
        longueur_ligne = largeur 
        draw.line([position_ligne, (position_ligne[0] + longueur_ligne, position_ligne[1])], fill=couleur_contours, width=largeur_bordure)


        font_mentions = ImageFont.truetype("ArchivoNarrow-Bold.ttf", 20)
        picture = "Photo: " + data.auteur
        via = "via: " + data.via
        if(data.auteur != ''):
            mentions_text = picture + " \n " + via 
        else : 
            mentions_text = via
        mentions_text_color = (255, 255, 255)  


       
        textbbox = draw.textbbox((0, 0), mentions_text, font=font_mentions)

        text_width = textbbox[2] - textbbox[0]


        max_x = image.width - text_width - 10  
        max_y = 10  

        x = min(max_x, max(10, max_x)) 

        draw.text((x, max_y), mentions_text, fill=mentions_text_color, font=font_mentions)



        font_size = 42
        
        if len(data.headline) < 30:
            font_size = 92
        elif 30 < len(data.headline) < 50:
            font_size = 82
        elif 50 < len(data.headline) < 75:
            font_size = 62
        elif 75 < len(data.headline) < 100:
            font_size = 52
        elif 100 < len(data.headline) < 150:
            font_size = 48
        elif 150 < len(data.headline) < 175:
            font_size = 32
        else:
            font_size = 32
            
        text = data.headline
        text_color = (0, 0, 0)

        font = ImageFont.truetype("ArchivoNarrow-Bold.ttf", font_size)  

        textbbox = draw.textbbox((0, 0), text, font=font)
        text_width = textbbox[2] - textbbox[0]
        
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

            centered_lines = []
            for line in lines:
                line_bbox = draw.textbbox((0, 0), line, font=font)
                line_width = line_bbox[2] - line_bbox[0]
                centered_x = (max_width - line_width) / 2 + 10
                centered_lines.append((line, centered_x))

            return centered_lines

        wrapped_and_centered_lines = wrap_and_center_text(text, font, largeur - 35)
        line_spacing = 10
        current_y = point_depart[1] + 30
        for line, centered_x in wrapped_and_centered_lines:
            textbbox = draw.textbbox((0, 0), line, font=font)
            text_height = textbbox[3] - textbbox[1]

            if current_y + text_height <= point_fin[1]:
                x = centered_x  
                y = current_y  
                draw.text((x, y), line, fill=text_color, font=font)
                current_y += text_height + line_spacing  

        # Obtenez les dimensions de l'image
        image_width, image_height = image.size

        # Définissez la taille et la position du rectangle au milieu de l'image
        rect_width = 150
        rect_height = 50
        rect_x = (image_width - rect_width) // 2  # Au milieu horizontalement
        rect_y = (image_height - rect_height) // 1.48  # Un quart de la hauteur de l'image depuis le haut

        # Définissez la couleur du rectangle
        rect_color = (197,68,62)  # Rouge

        # Dessinez le rectangle
        draw.rectangle([rect_x, rect_y, rect_x + rect_width, rect_y + rect_height], fill=rect_color)

        # Définissez la couleur du texte et sa police
        text_color = (255, 255, 255)  # Blanc
        date_font = ImageFont.truetype("ArchivoNarrow-Bold.ttf", 46)  # Choisissez la taille de police souhaitée

        # Obtenez la date actuelle
        now = "report"

        # Obtenez les dimensions du texte
        textbbox = draw.textbbox((0, 0), now, font=date_font)
        text_width = textbbox[2] - textbbox[0]
        text_height = textbbox[3] - textbbox[1]

        # Calculez la position du texte au centre du rectangle


        # Dessinez la date au centre du rectangle
        draw.text((345, 494), now, fill=text_color, font=date_font)


        filename = str(uuid.uuid4()) + ".jpg"
        unique_filename = 'download-image/' + filename

        # Chargez le logo
        logo = Image.open("logo.png")

        # Redimensionnez le logo selon vos besoins
        logo.thumbnail((100, 100))  # Ajustez la taille du logo selon vos préférences

        # Superposez le logo en haut à gauche de l'image principale
        image.paste(logo, (10, 10), logo)

        image.save(unique_filename)

        json_file_path = 'bdd_image.json'

        with open(json_file_path, 'r') as json_file:
            contenu_json = json.load(json_file)

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        nouvel_objet = {'name_image': filename, 'caption': data.caption, 'date': now}

        contenu_json.append(nouvel_objet)

        with open(json_file_path, 'w') as json_file:
            json.dump(contenu_json, json_file, indent=4)


        return {'message': 'Image téléchargée avec succès', 'filename': filename}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/image/{filename}")
def get_image(filename: str):

    chemin_image = f"./download-image/{filename}"  


    if os.path.exists(chemin_image):

        return FileResponse(chemin_image, media_type="image/jpeg")
    else:
        raise HTTPException(status_code=404, detail="Image not found")
    
templates = Jinja2Templates(directory="templates")

@app.get("/show-pictures", response_class=HTMLResponse)
async def afficher_fichier_html(request: Request):

    with open('bdd_image.json', 'r') as json_file:
        contenu_json = json.load(json_file)

    contenu_json.sort(key=lambda x: x['date'], reverse=True)
    return templates.TemplateResponse("template.html", {"request": request, "donnees": contenu_json})
