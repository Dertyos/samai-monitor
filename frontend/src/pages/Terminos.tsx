import { Link } from "react-router-dom";
import s from "./Legal.module.css";

export default function Terminos() {
  return (
    <div className={s.legal}>
      <Link to="/" className={s.backLink}>&larr; Volver al inicio</Link>
      <h1>Condiciones del Servicio</h1>
      <p className={s.updated}>Ultima actualizacion: 3 de abril de 2026</p>

      <h2>1. Aceptacion de los terminos</h2>
      <p>
        Al registrarse o utilizar Alertas Judiciales ("el Servicio"), usted
        acepta estas condiciones en su totalidad. Si no esta de acuerdo, no
        utilice el Servicio. El uso continuado despues de modificaciones
        constituye aceptacion de los terminos actualizados.
      </p>

      <h2>2. Descripcion del servicio</h2>
      <p>
        Alertas Judiciales es una plataforma que consulta informacion publica
        de los sistemas SAMAI (Consejo de Estado) y la Rama Judicial de Colombia
        para detectar nuevas actuaciones en procesos judiciales registrados por
        el usuario. El Servicio notifica al usuario por correo electronico
        cuando se detectan novedades.
      </p>

      <h2>3. Registro y cuenta</h2>
      <ul>
        <li>Debe ser mayor de edad para usar el Servicio.</li>
        <li>Debe proporcionar informacion veraz y actualizada al registrarse.</li>
        <li>Es responsable de mantener la confidencialidad de sus credenciales de acceso.</li>
        <li>Debe notificarnos inmediatamente a <a href="mailto:soporte@dertyos.com">soporte@dertyos.com</a> si detecta uso no autorizado de su cuenta.</li>
        <li>Una persona puede mantener una sola cuenta en el Servicio.</li>
      </ul>

      <h2>4. Uso aceptable</h2>
      <p>Usted se compromete a:</p>
      <ul>
        <li>Usar el Servicio unicamente para monitoreo legitimo de procesos judiciales.</li>
        <li>No intentar acceder a datos de otros usuarios ni a areas restringidas del sistema.</li>
        <li>No realizar scraping automatizado, ingenieria inversa, ni ataques de denegacion de servicio.</li>
        <li>No usar el Servicio para actividades ilegales o que infrinjan derechos de terceros.</li>
        <li>No revender ni redistribuir el acceso al Servicio sin autorizacion.</li>
      </ul>
      <p>
        El incumplimiento de estas condiciones puede resultar en la suspension
        o cancelacion inmediata de su cuenta.
      </p>

      <h2>5. Fuentes de informacion</h2>
      <p>
        El Servicio consulta fuentes publicas externas (SAMAI, Rama Judicial)
        que son operadas por entidades del Estado colombiano. <strong>No
        garantizamos la disponibilidad, exactitud, completitud ni oportunidad
        de la informacion proporcionada por dichas fuentes.</strong> Si las
        fuentes externas no estan disponibles, el Servicio puede no detectar
        actuaciones temporalmente.
      </p>

      <h2>6. Limitacion de responsabilidad</h2>
      <ul>
        <li>
          Alertas Judiciales <strong>no reemplaza</strong> la consulta directa
          de los despachos judiciales ni constituye asesoria legal.
        </li>
        <li>
          No somos responsables por decisiones tomadas con base en la informacion
          mostrada en la plataforma.
        </li>
        <li>
          No somos responsables por perdidas, danos directos o indirectos
          derivados del uso o imposibilidad de uso del Servicio.
        </li>
        <li>
          Nuestra responsabilidad total no excedera el monto pagado por usted
          en los ultimos 12 meses por el Servicio.
        </li>
      </ul>

      <h2>7. Disponibilidad</h2>
      <p>
        Nos esforzamos por mantener el Servicio disponible las 24 horas del dia,
        los 7 dias de la semana. Sin embargo, no garantizamos disponibilidad
        ininterrumpida. Podemos realizar mantenimientos programados o de
        emergencia, y procuraremos notificar con antelacion cuando sea posible.
      </p>

      <h2>8. Propiedad intelectual</h2>
      <p>
        El codigo fuente, diseno, marca, logotipo y contenido de Alertas
        Judiciales son propiedad exclusiva de Dertyos y estan protegidos por
        las leyes de propiedad intelectual de Colombia. El usuario conserva
        la propiedad de los datos que ingresa en la plataforma.
      </p>

      <h2>9. Planes y pagos</h2>
      <ul>
        <li>El Servicio ofrece planes gratuitos y de pago.</li>
        <li>Los terminos especificos de cada plan (limites, precios, periodos de facturacion) se detallan en la pagina de precios.</li>
        <li>Nos reservamos el derecho de modificar precios con al menos 30 dias de antelacion.</li>
        <li>Los pagos no son reembolsables, excepto cuando lo exija la ley aplicable.</li>
      </ul>

      <h2>10. Cancelacion y terminacion</h2>
      <ul>
        <li>Puede cancelar su cuenta en cualquier momento desde la seccion de Perfil.</li>
        <li>Al cancelar, perdera acceso inmediato al Servicio.</li>
        <li>Sus datos seran eliminados conforme a nuestra <Link to="/privacidad">Politica de Privacidad</Link>.</li>
        <li>Nos reservamos el derecho de suspender o cancelar cuentas que violen estas condiciones.</li>
      </ul>

      <h2>11. Modificaciones a los terminos</h2>
      <p>
        Podemos modificar estas condiciones en cualquier momento. Los cambios
        significativos se notificaran por correo electronico con al menos 15
        dias de anticipacion. Si no esta de acuerdo con los nuevos terminos,
        puede cancelar su cuenta antes de que entren en vigor.
      </p>

      <h2>12. Legislacion aplicable y jurisdiccion</h2>
      <p>
        Estas condiciones se rigen por las leyes de la Republica de Colombia.
        Las partes acuerdan someterse a la jurisdiccion de los tribunales
        competentes de Bogota D.C., Colombia, para la resolucion de cualquier
        controversia derivada de estas condiciones.
      </p>

      <h2>13. Contacto</h2>
      <p>
        Para preguntas sobre estas condiciones, escriba a{" "}
        <a href="mailto:soporte@dertyos.com">soporte@dertyos.com</a>.
      </p>
    </div>
  );
}
