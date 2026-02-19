import face_recognition
import numpy as np
import json
import cv2

def obtener_encoding(foto_path):
    """Obtiene el encoding facial de una foto"""
    imagen = face_recognition.load_image_file(foto_path)
    encodings = face_recognition.face_encodings(imagen)
    
    if len(encodings) == 0:
        return None  # no se detectó ningún rostro
    
    return encodings[0].tolist()  # convertimos a lista para guardar en BD

def comparar_rostro(encoding_guardado, foto_path):
    """Compara un rostro con el encoding guardado"""
    imagen = face_recognition.load_image_file(foto_path)
    encodings_foto = face_recognition.face_encodings(imagen)
    
    if len(encodings_foto) == 0:
        return False
    
    encoding_conocido = np.array(json.loads(encoding_guardado))
    resultado = face_recognition.compare_faces([encoding_conocido], encodings_foto[0], tolerance=0.5)
    
    return resultado[0]

def capturar_foto(nombre_archivo):
    """Captura una foto desde la cámara"""
    camara = cv2.VideoCapture(0)
    
    print("Presiona ESPACIO para tomar la foto, ESC para cancelar")
    
    while True:
        ret, frame = camara.read()
        cv2.imshow("Capturar foto", frame)
        
        tecla = cv2.waitKey(1)
        if tecla == 32:  # ESPACIO
            cv2.imwrite(nombre_archivo, frame)
            print(f"Foto guardada: {nombre_archivo}")
            break
        elif tecla == 27:  # ESC
            nombre_archivo = None
            break
    
    camara.release()
    cv2.destroyAllWindows()
    return nombre_archivo