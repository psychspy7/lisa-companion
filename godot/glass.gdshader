shader_type canvas_item;
render_mode unshaded;
uniform sampler2D screen_texture : hint_screen_texture, repeat_disable, filter_linear_mipmap;
void fragment() {
 vec4 blurred = textureLod(screen_texture, SCREEN_UV, 2.0);
 vec2 half_size = vec2(0.5);
 vec2 q = abs(UV - half_size) - vec2(0.483, 0.32);
 float distance = length(max(q, vec2(0.0))) + min(max(q.x, q.y), 0.0) - 0.018;
 float mask = 1.0 - smoothstep(-0.005, 0.005, distance);
 COLOR = vec4(mix(blurred.rgb, vec3(0.065,0.043,0.055),0.38), 0.76*mask);
}
