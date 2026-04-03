import { Link } from "react-router-dom";
import s from "./Legal.module.css";

export default function Privacidad() {
  return (
    <div className={s.legal}>
      <Link to="/" className={s.backLink}>&larr; Volver al inicio</Link>
      <h1>Politica de Privacidad</h1>
      <p className={s.updated}>Ultima actualizacion: 3 de abril de 2026</p>

      <h2>1. Responsable del tratamiento</h2>
      <p>
        <strong>Alertas Judiciales</strong> es un servicio operado por Dertyos,
        con domicilio en Bogota, Colombia.
      </p>
      <ul>
        <li>Correo de contacto: <a href="mailto:soporte@dertyos.com">soporte@dertyos.com</a></li>
        <li>Sitio web: <a href="https://alertas-judiciales.dertyos.com">alertas-judiciales.dertyos.com</a></li>
      </ul>

      <h2>2. Datos que recopilamos</h2>
      <p>Recopilamos unicamente los datos necesarios para proveer el servicio:</p>
      <ul>
        <li>
          <strong>Datos de cuenta:</strong> correo electronico. Si inicia sesion
          con Google, tambien recibimos su nombre y foto de perfil desde su
          cuenta de Google.
        </li>
        <li>
          <strong>Datos de uso:</strong> numeros de radicado judicial que usted
          registra voluntariamente para monitoreo, etiquetas personalizadas y
          preferencias de notificacion.
        </li>
        <li>
          <strong>Datos tecnicos:</strong> direccion IP, tipo de navegador,
          sistema operativo y datos de sesion (tokens de autenticacion). No
          utilizamos cookies de rastreo ni analitica de terceros.
        </li>
      </ul>

      <h2>3. Datos obtenidos de Google</h2>
      <p>
        Si usted elige iniciar sesion con Google, solicitamos acceso a los
        siguientes ambitos (scopes) de su cuenta de Google:
      </p>
      <ul>
        <li><strong>email:</strong> su direccion de correo electronico, para identificar su cuenta.</li>
        <li><strong>profile:</strong> su nombre y foto de perfil, para personalizar la interfaz.</li>
        <li><strong>openid:</strong> verificacion de identidad mediante OpenID Connect.</li>
      </ul>
      <p>
        No accedemos a sus contactos, calendario, archivos de Drive ni ningun
        otro dato de Google mas alla de los indicados. Los datos de Google se
        usan exclusivamente para autenticacion e identificacion dentro de
        Alertas Judiciales.
      </p>

      <h2>4. Finalidad del tratamiento</h2>
      <ul>
        <li>Autenticar su identidad y proteger su cuenta.</li>
        <li>Proveer el servicio de monitoreo de actuaciones judiciales en SAMAI y Rama Judicial.</li>
        <li>Enviar alertas por correo electronico cuando se detecten nuevas actuaciones en sus procesos.</li>
        <li>Mejorar el funcionamiento del servicio.</li>
      </ul>

      <h2>5. Base legal</h2>
      <p>
        El tratamiento de sus datos se realiza con base en su consentimiento
        libre, previo, expreso e informado al registrarse en la plataforma,
        conforme a:
      </p>
      <ul>
        <li>Ley Estatutaria 1581 de 2012 (Proteccion de Datos Personales).</li>
        <li>Decreto Reglamentario 1377 de 2013.</li>
        <li>Decreto Unico Reglamentario 1074 de 2015 (Titulo 21, Capitulo 25).</li>
      </ul>
      <p>
        Proporcionar sus datos es voluntario. Sin embargo, algunos datos (correo
        electronico) son necesarios para el funcionamiento del servicio.
      </p>

      <h2>6. Comparticion y transferencia de datos</h2>
      <p>
        <strong>No vendemos, alquilamos ni compartimos sus datos personales con
        terceros para fines comerciales.</strong> Utilizamos los siguientes
        proveedores de infraestructura para operar el servicio:
      </p>
      <ul>
        <li><strong>Amazon Web Services (AWS)</strong> — alojamiento, base de datos y autenticacion. Servidores en EE.UU. (us-east-1).</li>
        <li><strong>Google</strong> — autenticacion federada (solo si usted elige iniciar sesion con Google).</li>
        <li><strong>Resend</strong> — envio de correos electronicos transaccionales (alertas).</li>
      </ul>
      <p>
        Al utilizar el servicio, usted autoriza la transferencia internacional
        de datos a los servidores de AWS en Estados Unidos, conforme al articulo
        26 de la Ley 1581 de 2012.
      </p>

      <h2>7. Retencion de datos</h2>
      <ul>
        <li>Sus datos se conservan mientras mantenga una cuenta activa.</li>
        <li>Las alertas de actuaciones se eliminan automaticamente despues de 7 dias.</li>
        <li>Si solicita la eliminacion de su cuenta, todos sus datos seran eliminados en un plazo maximo de 30 dias.</li>
      </ul>

      <h2>8. Derechos del titular</h2>
      <p>
        Conforme a la Ley 1581 de 2012, usted tiene derecho a:
      </p>
      <ul>
        <li><strong>Conocer</strong> sus datos personales almacenados.</li>
        <li><strong>Actualizar y rectificar</strong> datos inexactos, incompletos o desactualizados.</li>
        <li><strong>Solicitar la supresion</strong> de sus datos cuando no sean necesarios para la finalidad.</li>
        <li><strong>Revocar</strong> el consentimiento otorgado para el tratamiento.</li>
        <li><strong>Presentar quejas</strong> ante la Superintendencia de Industria y Comercio (SIC).</li>
      </ul>
      <p>
        Para ejercer cualquiera de estos derechos, escriba a{" "}
        <a href="mailto:soporte@dertyos.com">soporte@dertyos.com</a> indicando
        su nombre, correo registrado y el derecho que desea ejercer. Responderemos
        en un plazo maximo de 15 dias habiles.
      </p>

      <h2>9. Seguridad</h2>
      <p>
        Implementamos medidas tecnicas y organizativas para proteger sus datos:
      </p>
      <ul>
        <li>Cifrado en transito (TLS/HTTPS) en todas las comunicaciones.</li>
        <li>Autenticacion segura mediante AWS Cognito con tokens JWT.</li>
        <li>Acceso restringido a la infraestructura con principio de minimo privilegio.</li>
        <li>Datos almacenados en DynamoDB con cifrado en reposo.</li>
      </ul>

      <h2>10. Eliminacion de datos</h2>
      <p>
        Usted puede eliminar su cuenta y todos sus datos en cualquier momento
        desde la seccion de Perfil de la aplicacion, o solicitandolo por correo
        a <a href="mailto:soporte@dertyos.com">soporte@dertyos.com</a>. La
        eliminacion incluye: datos de cuenta, radicados registrados, historial
        de alertas y etiquetas.
      </p>

      <h2>11. Cambios a esta politica</h2>
      <p>
        Podemos actualizar esta politica periodicamente. Notificaremos cambios
        significativos por correo electronico con al menos 15 dias de anticipacion.
        El uso continuado del servicio despues de la notificacion constituye
        aceptacion de los cambios.
      </p>
    </div>
  );
}
