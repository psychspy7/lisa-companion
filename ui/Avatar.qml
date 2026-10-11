import QtQuick

Item {
    id: avatar
    property url portrait
    property bool rigActive: false
    property bool animated: true
    property bool speaking: false
    property real audioLevel: 0
    property string mood: "smile"
    property real gazeX: 0
    property real gazeY: 0
    property real clock: 0
    property real blink: 0
    property real mouth: speaking ? Math.min(1, audioLevel * 2.1) : 0
    property real moodTilt: mood === "shy" || mood === "blushing" ? -0.018 : mood === "angry" || mood === "commanding" ? 0.018 : 0
    Behavior on mouth { NumberAnimation { duration: 55 } }
    Behavior on moodTilt { NumberAnimation { duration: 380; easing.type: Easing.InOutSine } }
    Behavior on gazeX { NumberAnimation { duration: 350; easing.type: Easing.OutCubic } }
    Behavior on gazeY { NumberAnimation { duration: 350; easing.type: Easing.OutCubic } }
    NumberAnimation on clock { from: 0; to: Math.PI * 200; duration: 900000; loops: Animation.Infinite; running: avatar.animated }
    Timer { interval: 3200 + Math.random() * 2400; running: avatar.animated && avatar.rigActive; repeat: true; onTriggered: { blinkAnimation.restart(); interval = 2800 + Math.random() * 3200 } }
    SequentialAnimation {
        id: blinkAnimation
        NumberAnimation { target: avatar; property: "blink"; to: 1; duration: 85; easing.type: Easing.InSine }
        PauseAnimation { duration: 35 }
        NumberAnimation { target: avatar; property: "blink"; to: 0; duration: 110; easing.type: Easing.OutSine }
    }
    Image { id: base; anchors.fill: parent; source: avatar.portrait; sourceSize: Qt.size(1440,2560); smooth: true; mipmap: true; visible: false }
    Image { id: eyes; source: "../assets/avatar/blink.png"; visible: false; smooth: true }
    Image { id: speech; source: "../assets/avatar/talk.png"; visible: false; smooth: true }
    ShaderEffect {
        objectName: "avatarRig"
        anchors.fill: parent
        property variant source: base
        property variant blinkTexture: eyes
        property variant talkTexture: speech
        property real clock: avatar.animated ? avatar.clock : 0
        property real blink: avatar.rigActive ? avatar.blink : 0
        property real mouth: avatar.rigActive ? avatar.mouth : 0
        property real headTilt: avatar.rigActive ? avatar.moodTilt + avatar.gazeX * 0.015 : 0
        property real nod: avatar.rigActive ? avatar.gazeY * 0.001 : 0
        property vector4d eyeA: Qt.vector4d(lisa.avatarSpec.eyes[0][0],lisa.avatarSpec.eyes[0][1],lisa.avatarSpec.eyes[0][2],lisa.avatarSpec.eyes[0][3])
        property vector4d eyeB: Qt.vector4d(lisa.avatarSpec.eyes[1][0],lisa.avatarSpec.eyes[1][1],lisa.avatarSpec.eyes[1][2],lisa.avatarSpec.eyes[1][3])
        property vector4d lips: Qt.vector4d(lisa.avatarSpec.mouth[0],lisa.avatarSpec.mouth[1],lisa.avatarSpec.mouth[2],lisa.avatarSpec.mouth[3])
        fragmentShader: "shaders/avatar.frag.qsb"
    }
}
