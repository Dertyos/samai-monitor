
## Bug Reportes
- **SAMAI Redirect "Ver en SAMAI"**: Al consultar la documentación en `DOCS`, se encontró que el verdadero parámetro `guid` usado por SAMAI es la concatenación del radicado formateado con guiones y el ID numérico de la Corporación. Se aplicó la corrección al frontend (`guid={radicadoFormato}{corporacion}`) en `DetalleRadicado.tsx`. **Pendiente**: Actualizar los correos generados por el Lambda `monitor` para que la url embebida incluya también la corporación.
