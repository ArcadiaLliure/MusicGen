# 🎵 MusicGen Studio (Arcàdia Lliure)

Un portal web avançat i complet per a la generació musical amb Intel·ligència Artificial, dissenyat per executar-se en local mitjançant Docker. Utilitza els potents models de **MusicGen** per transformar descripcions de text en pistes d'àudio d'alta qualitat.

## ✨ Característiques Principals

- **Generació Lliure i Guiada:** Genera música amb prompts lliures o utilitza el *Wizard d'Instruments* (Obligatori, Opcional, Prohibit) per afinar la teva orquestració.
- **Mode Àlbum Secuencial:** Crea àlbums sencers on cada pista s'encadena harmònicament amb l'anterior (requereix el model `MusicGen Melody`), actuant com a inspiració d'àudio de forma totalment automàtica.
- **Cua de Treball Intel·ligent:** Llança desenes de pistes de cop. El sistema les encolarà i les processarà d'una en una, evitant saturar la VRAM de la targeta gràfica (GPU).
- **Gestió de la Biblioteca:** Totes les creacions es desen en una base de dades SQLite local. Reprodueix, elimina o gestiona les teves pistes i àlbums des de la pestanya "Biblioteca".
- **Metadades Nadius (ID3):** Quan la música es genera, el títol, l'artista i l'àlbum queden escrits de forma permanent en les propietats de l'arxiu binari `.wav`.

## 🚀 Instal·lació i Ús

### Requisits
- Docker i Docker Compose.
- Una targeta gràfica NVIDIA amb suport CUDA (es recomanen almenys 8-12GB de VRAM per usar els models *Large*).

### Instruccions
1. Obre un terminal a la carpeta principal del projecte.
2. Construeix i aixeca el contenidor en segon pla:
   ```bash
   docker compose up -d --build
   ```
3. Obre el teu navegador web preferit (com Firefox o Chrome) i accedeix a:
   ```
   http://localhost:8000
   ```
*(Nota: La primera vegada que seleccionis un model específic, pot trigar uns minuts mentre descarrega els pesos del model (entre 1.5GB i 3.3GB) i els emmagatzema a la carpeta local `./model_cache`).*

## 👏 Crèdits i Agraïments

Aquest projecte no seria possible sense la feina pionera de la comunitat Open Source i d'IA:

- **[Meta AI Research (Audiocraft)](https://github.com/facebookresearch/audiocraft):** Als enginyers i investigadors de Meta per obrir i compartir la tecnologia i els models de *MusicGen*. Són el veritable motor d'aquesta eina.
- **[Hugging Face](https://huggingface.co/):** Per proporcionar la infraestructura gratuïta per a descarregar els pesos dels models de manera àgil.
- **Arcàdia Lliure (Manel & AI):** Desenvolupament de l'arquitectura del servidor (Flask/SQLite), el sistema de cues, la persistència de metadades i el disseny complet del portal d'usuari Front-End (SPA).

## 📄 Llicència i Propietat

Aquest producte i la seva integració web (excloent els models base de Meta/Audiocraft) són propietat d'**Arcàdia Lliure**.

© 2026 Arcàdia Lliure. Tots els drets reservats.
