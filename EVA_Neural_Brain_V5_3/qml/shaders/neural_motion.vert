VARYING vec2 uv;
VARYING float seed;
VARYING float emission;
void MAIN() {
    uv = UV0;
    seed = UV1.x;
    // Recuperar el centro del quad: sus seis vértices siguen la misma trayectoria.
    vec3 corner = vec3(UV0 * UV1.y, 0.0);
    vec3 center = VERTEX - corner;
    vec3 radial = normalize(center + vec3(.001));
    float phase = uTime * 6.28318530718 / 4096.0;
    float offset = seed * 6.28318530718;
    float organic = .82+.18*sin(phase*53.0+offset*2.0);
    vec3 calm = vec3(sin(phase*97.0+offset), cos(phase*71.0+offset*2.0),
                     sin(phase*83.0+offset*3.0)) * .95 * organic;
    // Escaneo ascendente: las zonas alcanzadas atraen suavemente los puntos.
    float scan = .5+.5*sin(phase*587.0-center.y*.037);
    vec3 focus = vec3(35.0*sin(phase*113.0),18.0*cos(phase*89.0),0.0);
    vec3 reception = normalize(focus-center+vec3(.001));
    vec3 listening = reception*(2.0+5.0*scan)*organic
        + vec3(sin(phase*457.0+offset)*2.3, sin(phase*653.0+offset)*3.3, 0.0);
    // Remolinos locales alternos: más rápidos, sin girar la anatomía completa.
    vec3 tangent = normalize(vec3(-center.y, center.x, 18.0));
    vec3 processing = tangent*(8.5*sin(phase*1693.0+offset))*organic
        + radial*(4.0*cos(phase*1231.0+offset*2.0))
        + vec3(0.0, 3.0*sin(phase*1877.0+offset), 5.0*cos(phase*1451.0+offset));
    // Ondas de emisión: el desfase radial desplaza el frente hacia fuera.
    float wave = sin(phase*1173.0-length(center)*.055);
    vec3 speaking = radial*(3.5+6.0*wave) + calm*.4;
    // Mantener la onda anterior, atenuada durante silencios de la envolvente.
    // Desfases deterministas pequeños; la malla cortical nunca se deforma.
    speaking *= 1.0-.85*uSpeechMix;
    float nearCore = 1.15-.25*smoothstep(20.0,140.0,length(center));
    float syllable = uSpeechLevel * nearCore;
    float localWave = .85+.15*sin(phase*1173.0+offset*.65);
    speaking += uSpeechJumpStrength * syllable * (
        radial*(10.0*localWave + 3.0*uSpeechWaveBoost*wave)
        + tangent*(1.1*sin(phase*653.0+offset)));
    // Perturbación acotada, continua; sin ruido nuevo ni flashes discontinuos.
    vec3 tension = vec3(sin(phase*2017.0+offset)+.35*sin(phase*3049.0+offset*3.0),
                        cos(phase*1741.0+offset*2.0), sin(phase*2399.0+offset)) * 2.4;
    float waitingPulse = .5+.5*sin(phase*239.0-length(center)*.025);
    float idle = max(0.0, 1.0-uListening-uProcessing-uSpeaking-uError-uStandby-uWaiting);
    vec3 displacement = calm*(idle+.08*uStandby+.35*uWaiting) + radial*waitingPulse*.6*uWaiting + listening*uListening
        + processing*uProcessing + speaking*uSpeaking + tension*uError;
    // Emisión ligada al frente de habla y recepción; los destellos no son un reloj separado.
    emission = .65 + .18*idle + .25*uListening*scan
        + uProcessing*(.25+.25*sin(phase*1231.0+offset))
        + uSpeaking*((.15+.8*pow(.5+.5*wave,2.0))*(1.0-.6*uSpeechMix)
                     + uSpeechLevel*uSpeechGlowBoost) + .15*uWaiting*waitingPulse;
    emission *= 1.0-.45*uStandby;
    // Sólo se desplazan nodos, dentro de la esfera. Malla y filamentos quedan fijos.
    POSITION = MODELVIEWPROJECTION_MATRIX * vec4(center+displacement*uMotionScale+corner, 1.0);
}
