#version 440
layout(location = 0) in vec2 qt_TexCoord0;
layout(location = 0) out vec4 fragColor;
layout(std140, binding = 0) uniform buf {
    mat4 qt_Matrix;
    float qt_Opacity;
    float clock;
    float blink;
    float mouth;
    float headTilt;
    float nod;
    vec4 eyeA;
    vec4 eyeB;
    vec4 lips;
} ubuf;
layout(binding = 1) uniform sampler2D source;
layout(binding = 2) uniform sampler2D blinkTexture;
layout(binding = 3) uniform sampler2D talkTexture;
float ellipse(vec2 uv, vec2 center, vec2 radius) {
    return 1.0 - smoothstep(0.72, 1.0, length((uv-center)/radius));
}
void main() {
    vec2 uv=qt_TexCoord0;
    float upper=1.0-smoothstep(0.13,0.23,uv.y);
    float turn=(sin(ubuf.clock*0.62)*0.009+ubuf.headTilt)*upper;
    vec2 pivot=vec2(0.493,0.174);
    vec2 delta=uv-pivot;
    uv=pivot+mat2(cos(turn),-sin(turn),sin(turn),cos(turn))*delta;
    uv.y+=ubuf.nod*upper;
    float hair=smoothstep(0.13,0.24,uv.y)*(1.0-smoothstep(0.44,0.53,uv.y));
    float outer=smoothstep(0.10,0.24,abs(uv.x-0.50));
    uv.x+=sin(ubuf.clock*0.8+uv.y*11.0)*0.0017*hair*outer;
    uv.y+=sin(ubuf.clock)*0.0007*smoothstep(0.19,0.28,uv.y)*(1.0-smoothstep(0.45,0.55,uv.y));
    vec4 base=texture(source,uv);
    // Only the eye and mouth regions use edited expression frames. Outfits remain intact.
    float eyeMask=max(ellipse(uv,ubuf.eyeA.xy,ubuf.eyeA.zw),ellipse(uv,ubuf.eyeB.xy,ubuf.eyeB.zw));
    float mouthMask=ellipse(uv,ubuf.lips.xy,ubuf.lips.zw);
    vec4 blink=texture(blinkTexture,uv);
    vec4 talk=texture(talkTexture,uv);
    base=mix(base,blink,eyeMask*ubuf.blink*blink.a);
    base=mix(base,talk,mouthMask*ubuf.mouth*talk.a);
    fragColor=base*ubuf.qt_Opacity;
}
