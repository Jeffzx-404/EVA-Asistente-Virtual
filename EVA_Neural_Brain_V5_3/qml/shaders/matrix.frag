#version 440
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    vec2 resolution;
    vec2 exclusionCenter;
    vec2 exclusionRadius;
    vec4 quietRect;
    vec4 panelRect;
    vec4 stateTint;
    float sceneTime;
    float lowDetail;
    float maskEnabled;
};
layout(binding = 1) uniform sampler2D glyphAtlas;

float hash(float n) {
    float p = fract(n*.1031);
    p *= p+33.33;
    return fract(p*(p+p));
}

float quiet(vec2 p, vec4 rect) {
    if (rect.z <= 0.0 || rect.w <= 0.0) return 1.0;
    vec2 d = abs(p-(rect.xy+rect.zw*.5))-rect.zw*.5;
    float distance = length(max(d,vec2(0)))+min(max(d.x,d.y),0.0);
    return mix(.12,1.0,smoothstep(-6.0,26.0,distance));
}

float glyph(vec2 uv, float digit) {
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) return 0.0;
    return texture(glyphAtlas,vec2((digit+uv.x)*.5,uv.y)).a;
}

void main() {
    vec2 p = qt_TexCoord0*resolution;
    float radius = length((p-exclusionCenter)/max(exclusionRadius,vec2(1)));
    float protection = mix(1.0,smoothstep(1.0,1.20,radius),maskEnabled);
    // Salida temprana: no calcular lluvia en la zona protegida.
    if (protection < .0001) { fragColor = vec4(0); return; }

    float spacing = mix(18.0,28.0,lowDetail);
    float column = floor(p.x/spacing);
    float seed = hash(column*13.7+51.3);
    float depth = hash(column*7.91+3.1);
    float cellHeight = mix(22.0,17.0,depth)+lowDetail*3.0;
    float speed = mix(19.0,48.0,depth)*(0.85+seed*.3);
    float shift = (seed-.5)*spacing*.22;
    float localX = (p.x-column*spacing-spacing*.5-shift)/mix(15.0,21.0,depth)+.5;
    float rowPosition = (p.y-sceneTime*speed)/cellHeight+seed*80.0;
    float row = floor(rowPosition);
    vec2 uv = vec2(localX,fract(rowPosition));

    float trailLength = 15.0+hash(column*4.3+9.0)*24.0;
    float period = trailLength+5.0+hash(column*9.7)*13.0;
    float behind = mod(-rowPosition+seed*period,period);
    float tail = pow(max(0.0,1.0-behind/trailLength),1.55);
    float head = exp(-pow(behind-.55,2.0)*3.0);
    // Desvanecer el comienzo del ciclo: evita que la cabeza aparezca de golpe.
    tail *= smoothstep(0.0,.35,behind);
    head *= smoothstep(0.0,.2,behind);

    float characterClock = sceneTime*(.55+seed*.30)+hash(row*3.13+column)*8.0;
    float epoch = floor(characterClock);
    float digitA = step(.5,hash(row*9.7+column*31.3+(epoch-1.0)*17.1));
    float digitB = step(.5,hash(row*9.7+column*31.3+epoch*17.1));
    float ink = mix(glyph(uv,digitA),glyph(uv,digitB),smoothstep(0.0,.16,fract(characterClock)));
    float glimmer = .80+.20*hash(row*2.7+column*5.1);
    float alpha = ink*(tail*.47+head*.48)*mix(.30,.82,depth)*glimmer;
    vec3 blue = mix(vec3(.035,.23,.52),vec3(.08,.56,.95),depth);
    blue = mix(blue,stateTint.rgb,.08);
    vec3 tint = mix(blue,vec3(.52,.90,1.0),head*.8);

    float frameFade = smoothstep(0.0,18.0,p.y)*smoothstep(0.0,18.0,resolution.y-p.y);
    float header = mix(.18,1.0,smoothstep(48.0,108.0,p.y));
    alpha *= protection*frameFade*header*quiet(p,quietRect)*quiet(p,panelRect)*qt_Opacity;
    fragColor = vec4(tint*alpha,alpha); // Qt Quick espera color premultiplicado.
}
