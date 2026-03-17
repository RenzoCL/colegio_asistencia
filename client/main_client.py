import cv2
import face_recognition
import requests
import numpy as np

# CONFIGURACIÓN
# Cambia 'localhost' por la IP de tu PC Servidor si estás en otra computadora
SERVER_URL = "http://localhost:8000" 

def cargar_datos_servidor():
    print("Cargando encodings desde el servidor...")
    try:
        response = requests.get(f"{SERVER_URL}/alumnos/encodings")
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error conectando al servidor: {e}")
        return []

def iniciar_asistencia():
    # 1. Obtener los rostros conocidos del servidor
    datos_alumnos = cargar_datos_servidor()
    if not datos_alumnos:
        print("No hay alumnos registrados o el servidor está caído.")
        return

    known_face_encodings = [np.array(a['encoding']) for a in datos_alumnos]
    known_face_names = [a['nombres'] for a in datos_alumnos]
    known_face_ids = [a['id'] for a in datos_alumnos]

    video_capture = cv2.VideoCapture(0)

    print("Sistema de asistencia activo. Presiona 'q' para salir.")

    while True:
        ret, frame = video_capture.read()
        
        # Redimensionar para mayor velocidad en PCs básicas
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Localizar caras en el frame actual
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding in face_encodings:
            # Comparar con los alumnos de la DB
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
            name = "Desconocido"
            alumno_id = None

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            
            if matches[best_match_index]:
                name = known_face_names[best_match_index]
                alumno_id = known_face_ids[best_match_index]

                # ENVIAR ASISTENCIA AL SERVIDOR
                try:
                    res = requests.post(f"{SERVER_URL}/verificar-asistencia/{alumno_id}")
                    print(f"Respuesta del servidor: {res.json()['msg']} para {name}")
                except Exception as e:
                    print(f"Error al enviar asistencia: {e}")

            # Dibujar cuadro en la cara (Opcional, consume recursos)
            # Aquí podrías poner lógica para mostrar el nombre en pantalla

        cv2.imshow('Camara de Asistencia - Colegio', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    iniciar_asistencia()
