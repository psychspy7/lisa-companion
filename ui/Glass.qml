import QtQuick
import QtQuick.Effects

Item {
    id: glass
    property Item backdrop
    property real cornerRadius: 22
    property color tint: "#6516192d"
    property bool animate: true
    property point origin: { var bounds=[x,y,width,height,backdrop ? backdrop.width : 0,backdrop ? backdrop.height : 0]; return backdrop ? mapToItem(backdrop,0,0) : Qt.point(0,0) }
    ShaderEffectSource {
        id: sample
        sourceItem: glass.backdrop
        sourceRect: Qt.rect(glass.origin.x, glass.origin.y, glass.width, glass.height)
        textureSize: Qt.size(Math.max(16, glass.width / 2), Math.max(16, glass.height / 2))
        live: glass.visible && glass.animate
        visible: false
    }
    Rectangle { id: mask; width: glass.width; height: glass.height; radius: glass.cornerRadius; color: "white"; visible: false; layer.enabled: true }
    MultiEffect { anchors.fill: parent; source: sample; blurEnabled: true; blur: 0.8; blurMax: 32; autoPaddingEnabled: false; maskEnabled: true; maskSource: mask }
    Rectangle { anchors.fill: parent; radius: glass.cornerRadius; color: glass.tint; border.color: "#55e6defc"; border.width: 1 }
    Rectangle { x: glass.cornerRadius; y: 1; width: Math.max(0, glass.width - glass.cornerRadius * 2); height: 1; color: "#75ffffff"; opacity: 0.45 }
}
