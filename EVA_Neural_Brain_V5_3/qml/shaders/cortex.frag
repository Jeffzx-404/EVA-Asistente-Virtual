VARYING vec3 worldNormal;
VARYING vec3 viewDirection;
VARYING vec3 localPosition;
void MAIN() {
    vec3 n = normalize(worldNormal);
    vec3 v = normalize(viewDirection);
    float rim = pow(1.0 - abs(dot(n, v)), 2.2);
    float key = max(dot(n, normalize(vec3(-.45, .7, .65))), 0.0);
    float fill = max(dot(n, normalize(vec3(.65, -.15, .65))), 0.0);
    float scan = pow(.5 + .5 * sin(localPosition.y * 1.5), 18.0);
    float wave = .94 + .06 * sin(uTime * 6.28318530718 / 4096.0 * 1043.0 + localPosition.x * .025);
    vec3 tint = mix(uTint, uSecondary, .22 + fill*.25);
    // Emisión aditiva baja: no oscurece las conexiones posteriores y no acumula
    // varias capas opacas. Las normales mantienen visibles los surcos y el contorno.
    vec3 color = tint * (.012 + key * .08 + rim * .64) * wave;
    color += tint * scan * .008;
    vec3 anatomy = vec3(.46,.53,.66) * (.15 + key*.9 + fill*.18);
    FRAGCOLOR = vec4(mix(color, anatomy, uAnatomy), mix(.105, 1.0, uAnatomy));
}
