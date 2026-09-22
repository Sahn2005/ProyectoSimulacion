# Problematica del servicio electrico 
# Simulación: Respaldo Solar en el Barrio Kennedy, Ciénaga (Magdalena)

Proyecto para Webots que representa la propuesta: instalar paneles solares
de respaldo en el barrio Kennedy, afectado por la inestabilidad del servicio
eléctrico en Ciénaga, para que cuando la red falle, las viviendas mantengan
la luz gracias a energía solar almacenada en batería.

## Qué vas a ver en la simulación

El barrio Kennedy dividido en dos zonas de 18 casas cada una (dos bloques
de 9, uno a cada lado de la calle principal), para comparar el antes y el
después de la propuesta dentro del mismo barrio:

| Zona                          | ¿Tiene panel solar de respaldo? | Qué pasa durante un corte |
|-------------------------------|----------------------------------|----------------------------|
| Kennedy - sin panel solar (18 casas) | No                          | Se quedan completamente a oscuras (situación actual) |
| Kennedy - con panel solar (18 casas) | Sí                          | Las casas quedan iluminadas en **verde** (batería solar) |

Las casas están diseñadas para parecerse a las del barrio: fachadas de
bloque de concreto sin pintar o pintadas en tonos sencillos y desgastados,
techos de placa de concreto o lámina de zinc, y rejas de seguridad en las
ventanas — nada de colores vivos ni estilo colonial, que no es representativo
de este sector.

Cada cierto tiempo la torre eléctrica del barrio "falla" (se pone roja
intermitente) y las ventanas de las 36 casas reaccionan según la zona.
Además se abren **dos ventanas flotantes** aparte del mundo 3D:

- **"hud"** — estado en vivo de la red: si está arriba o caída, cuántos
  cortes van simulados, y el nivel de batería (%) de la zona con panel solar.
- **"cronograma"** — el cronograma de 3 meses del proyecto (ver más abajo),
  **sincronizado con el reloj de la simulación**: la fase activa se resalta
  sola y una barra de progreso avanza en tiempo real, sin que tengas que
  tocar nada.

  Integrantes
  - Adrian Zarate 
  - Sebastian Hernandez
  - Juan Hernandez
