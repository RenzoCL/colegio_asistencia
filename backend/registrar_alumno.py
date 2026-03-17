import cv2
import face_recognition
import requests
import json

def enrolar():
    print("--- REGISTRO DE NUEVO ALUMNO ---")
    dni = input("DNI: ")
    nombres = input("Nombres completos: ")
    grado = input("Grado: ")
    seccion = input("Sección: ")
    nivel = input("Nivel (Primaria/Secundaria): ")

    video_capture = cv2.VideoCapture(0)
    print("Mira a la cámara. Presiona 'S' para capturar la foto.")

    while True:
        ret, frame = video_capture.read()
        cv2.imshow('Registro Facial', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('s'):
            # Convertir de BGR (OpenCV) a RGB (face_recognition)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            encodings = face_recognition.face_encodings(rgb_frame)

            if len(encodings) > 0:
                encoding_list = encodings[0].tolist() # Convertir a lista para JSON
                
                # Enviar al servidor local
                payload = {
                    "dni": dni, "nombres": nombres, "grado": grado,
                    "seccion": seccion, "nivel": nivel, "encoding": encoding_list
                }
                
                try:
                    res = requests.post("http://localhost:8000/alumnos/registrar", json=payload)
                    print(res.json()["message"])
                except Exception as e:
                    print(f"Error conectando al servidor: {e}")
                break
            else:
                print("No se detectó ningún rostro. Intenta de nuevo.")

    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    enrolar()
