import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtMultimedia

ApplicationWindow {
    id: root
    visible: false
    width: 1440; height: 900
    minimumWidth: 800; minimumHeight: 560
    title: "LISA · Kitty Corp"
    color: "#101523"
    property bool chatVisible: true
    property bool historyVisible: false
    property real zoom: lisa.initialZoom
    property real characterOffsetX: 0
    property real characterOffsetY: 0
    property string currentPortrait: lisa.portrait
    property string previousPortrait: ""
    property real dissolve: 1
    property bool ambientMotion: lisa.motionEnabled && visible && visibility !== Window.Minimized
    property string clipUrl: ""
    property bool clipVisible: clipUrl !== "" && player.playbackState === MediaPlayer.PlayingState
    property real pointerX: 0
    property real pointerY: 0
    Component.onCompleted: { root.clipUrl=lisa.motionClip; player.source=root.clipUrl; if (root.clipUrl) player.play() }
    onVisibilityChanged: { if (root.visibility===Window.Minimized) player.pause(); else if (root.clipUrl) player.play() }
    onClosing: lisa.quit()
    Shortcut { sequence: "F11"; onActivated: root.visibility === Window.FullScreen ? root.showNormal() : root.showFullScreen() }
    Shortcut { sequence: "Escape"; onActivated: { lisa.stop(); root.historyVisible=false; if (root.visibility === Window.FullScreen) root.showNormal() } }
    Shortcut { sequence: "Ctrl+H"; onActivated: root.chatVisible=!root.chatVisible }
    Shortcut { sequence: "Ctrl+J"; onActivated: root.historyVisible=!root.historyVisible }
    component SoftButton: Button {
        id: button
        property bool accent: false
        font.family: "Segoe UI"; font.pixelSize: 12
        padding: 10; implicitHeight: 36
        contentItem: Text { text: button.text; color: button.enabled ? "#f2ecff" : "#79798c"; font: button.font; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
        background: Rectangle { radius: 11; color: button.down ? "#995f4d85" : button.hovered ? "#6a9182bc" : button.accent ? "#70544886" : "#20ffffff"; border.width: 1; border.color: button.hovered ? "#99d8c4ff" : "#30eee4ff"; Behavior on color { ColorAnimation { duration: 150 } } }
    }
    Connections {
        target: lisa
        function onImageChanged(url) {
            if (url===root.currentPortrait) return;
            root.previousPortrait=root.currentPortrait; root.currentPortrait=url; root.dissolve=0; fade.restart()
        }
        function onClipChanged(url) {
            if (url===root.clipUrl) return;
            player.stop(); root.clipUrl=url; player.source=url; if (url) player.play()
        }
    }
    NumberAnimation { id: fade; target: root; property: "dissolve"; to: 1; duration: 420; easing.type: Easing.InOutSine; onFinished: root.previousPortrait="" }
    Item {
        id: scene
        objectName: "characterStage"
        anchors.fill: parent
        clip: true
        Image { anchors.fill: parent; source: lisa.background; fillMode: Image.PreserveAspectCrop; sourceSize.width: Math.min(3840,root.width*Screen.devicePixelRatio); smooth: true; mipmap: true }
        Rectangle { anchors.fill: parent; color: "#1010182d" }
        Rectangle { anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom; height: parent.height*0.35; gradient: Gradient { GradientStop { position: 0; color: "#00101523" } GradientStop { position: 1; color: "#a0101523" } } }
        MouseArea { anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton; onPositionChanged: function(mouse) { root.pointerX=(mouse.x/width-.5)*2; root.pointerY=(mouse.y/height-.5)*2 } onExited: { root.pointerX=0; root.pointerY=0 } }
        Rectangle {
            width: Math.min(300,root.width*.20)*root.zoom; height: 18; radius: height/2
            anchors.horizontalCenter: parent.horizontalCenter; anchors.horizontalCenterOffset: root.characterOffsetX
            y: character.y+character.height-12; color: "#55090919"; opacity: .7
        }
        Item {
            id: character
            objectName: "characterCanvas"
            width: height*0.5625
            height: Math.max(300,root.height-110)
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.horizontalCenterOffset: root.characterOffsetX
            y: 32+root.characterOffsetY
            scale: root.zoom; transformOrigin: Item.Bottom
            Avatar { anchors.fill: parent; portrait: root.previousPortrait; opacity: 1-root.dissolve; animated: false }
            Avatar { id: liveAvatar; objectName: "liveAvatar"; anchors.fill: parent; portrait: root.currentPortrait; opacity: root.dissolve; rigActive: lisa.avatarRigActive; animated: root.ambientMotion && !root.clipVisible; speaking: lisa.playingSpeech; audioLevel: lisa.audioLevel; mood: lisa.moodId; gazeX: root.pointerX; gazeY: root.pointerY }
            Item {
                objectName: "clipLayer"
                anchors.fill: parent; opacity: root.clipVisible ? 1 : 0
                Behavior on opacity { NumberAnimation { duration: 240 } }
                VideoOutput { id: video; objectName: "clipVideo"; anchors.fill: parent; fillMode: VideoOutput.PreserveAspectFit; visible: root.clipVisible && !lisa.clipGreenScreen }
                ShaderEffectSource { id: videoTexture; sourceItem: video; hideSource: lisa.clipGreenScreen; visible: false; live: root.clipVisible }
                ShaderEffect { anchors.fill: parent; visible: root.clipVisible && lisa.clipGreenScreen; property variant source: videoTexture; fragmentShader: "shaders/green.frag.qsb" }
            }
            MouseArea {
                anchors.fill: parent; cursorShape: pressed ? Qt.ClosedHandCursor : Qt.OpenHandCursor
                property point start; property point offset
                onPressed: function(mouse) { start=mapToItem(scene,mouse.x,mouse.y); offset=Qt.point(root.characterOffsetX,root.characterOffsetY) }
                onPositionChanged: function(mouse) { var p=mapToItem(scene,mouse.x,mouse.y); if (pressed) { root.characterOffsetX=Math.max(-root.width*.35,Math.min(root.width*.35,offset.x+p.x-start.x)); root.characterOffsetY=Math.max(-root.height*.3,Math.min(root.height*.2,offset.y+p.y-start.y)) } else { root.pointerX=(p.x/root.width-.5)*2; root.pointerY=(p.y/root.height-.5)*2 } }
                hoverEnabled: true
                onDoubleClicked: root.resetLayout()
                onWheel: function(wheel) { root.zoom=Math.max(.65,Math.min(1.8,root.zoom+wheel.angleDelta.y/2400)); lisa.saveLayout(root.zoom,390); wheel.accepted=true }
            }
        }
        MediaPlayer { id: player; objectName: "clipPlayer"; videoOutput: video; audioOutput: AudioOutput { muted: true } loops: MediaPlayer.Infinite; onErrorOccurred: { var failed=root.clipUrl; player.stop(); root.clipUrl=""; lisa.clipFailed(failed) } }
    }
    function resetLayout() { root.zoom=1; root.characterOffsetX=0; root.characterOffsetY=0; lisa.saveLayout(root.zoom,390) }
    Glass {
        id: controls
        objectName: "topControls"
        backdrop: scene; animate: root.ambientMotion
        x: 22; y: 20; width: toolbar.implicitWidth+20; height: 54; cornerRadius: 18
        RowLayout {
            id: toolbar; anchors.centerIn: parent; spacing: 8
            Image { objectName: "brandLogo"; Layout.preferredWidth: 34; Layout.preferredHeight: 34; source: "../assets/lisa-logo.jpg"; sourceSize.width: 96; smooth: true; mipmap: true }
            Column { spacing: 2; Text { text: "LISA"; color: "#f5efff"; font.pixelSize: 15; font.letterSpacing: 3 } Text { text: lisa.version; color: "#c0b2d8"; font.pixelSize: 9 } }
            SoftButton { objectName: "settingsButton"; text: "Settings"; onClicked: lisa.settings() }
            SoftButton { text: "⋯"; font.pixelSize: 20; onClicked: appMenu.popup(controls.x,controls.y+controls.height+8) }
        }
    }
    Text { objectName: "companionTagline"; x: 26; y: 84; text: "A little company. A little chaos."; color: "#c9bdde"; opacity: .75; font.pixelSize: 11; font.letterSpacing: .5 }
    Row {
        anchors.top: parent.top; anchors.right: parent.right; anchors.margins: 22; spacing: 8
        SoftButton { text: root.visibility===Window.FullScreen ? "↙" : "⛶"; ToolTip.text: "Fullscreen · F11"; ToolTip.visible: hovered; onClicked: root.visibility===Window.FullScreen ? root.showNormal() : root.showFullScreen() }
        SoftButton { text: "×"; ToolTip.text: "Quit Lisa"; ToolTip.visible: hovered; onClicked: lisa.quit() }
    }
    Glass {
        id: subtitle
        objectName: "replyBubble"
        backdrop: scene; animate: root.ambientMotion; cornerRadius: 20; tint: "#4916192d"
        visible: root.chatVisible && lisa.lastReply!=="" && !root.historyVisible
        anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: dock.top; anchors.bottomMargin: 14
        width: Math.min(650,root.width-140); height: Math.min(100,replyText.implicitHeight+28)
        Text { id: replyText; anchors.fill: parent; anchors.margins: 14; text: lisa.lastReply.length>280 ? lisa.lastReply.slice(0,277)+"…" : lisa.lastReply; textFormat: Text.PlainText; wrapMode: Text.Wrap; elide: Text.ElideRight; maximumLineCount: 3; color: "#faf5ff"; font.pixelSize: 14; lineHeight: 1.15; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.historyVisible=true }
    }
    Glass {
        id: dock
        objectName: "chatPanel"
        backdrop: scene; animate: root.ambientMotion; tint: "#58161b2d"; cornerRadius: 24
        visible: root.chatVisible
        anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin: 22
        width: Math.min(760,root.width-64); height: composerRow.height+62
        Column {
            anchors.fill: parent; anchors.margins: 12; spacing: 8
            RowLayout {
                id: composerRow; width: parent.width; height: Math.max(36,Math.min(64,composer.contentHeight+14)); spacing: 8
                SoftButton { objectName: "conversationButton"; text: lisa.conversation ? "■ End talk" : "◉ Talk"; accent: lisa.conversation; onClicked: lisa.toggleConversation(); ToolTip.text: "Continuous voice conversation"; ToolTip.visible: hovered }
                TextArea { id: composer; objectName: "composer"; Layout.fillWidth: true; Layout.fillHeight: true; placeholderText: lisa.conversation ? "Or type while we talk…" : "Say something, Sir…"; placeholderTextColor: "#b8adc8"; color: "#ffffff"; wrapMode: TextEdit.Wrap; selectByMouse: true; font.pixelSize: 14; background: null; Keys.onReturnPressed: function(event) { if (!(event.modifiers & Qt.ShiftModifier)) { if (!lisa.busy && text.trim()) { lisa.send(text); text="" } event.accepted=true } } }
                SoftButton { objectName: "micButton"; text: lisa.recording ? "Send voice" : lisa.conversation ? "Interrupt" : "Mic"; enabled: !lisa.busy || lisa.recording || lisa.conversation; onClicked: lisa.mic() }
                SoftButton { objectName: "sendButton"; text: "↑"; font.pixelSize: 19; accent: true; enabled: !lisa.busy && composer.text.trim()!==""; onClicked: { lisa.send(composer.text); composer.text="" } }
            }
            RowLayout {
                width: parent.width; height: 22; spacing: 8
                Rectangle { width: 5; height: 5; radius: 3; color: lisa.recording ? "#d8b9ff" : lisa.talking ? "#83d9e6" : "#a6cec3" }
                Text { objectName: "conversationStatus"; Layout.fillWidth: true; text: lisa.status; elide: Text.ElideRight; color: "#d1c5e0"; font.pixelSize: 10; ToolTip.text: lisa.status; ToolTip.visible: statusHover.containsMouse; MouseArea { id: statusHover; anchors.fill: parent; hoverEnabled: true; acceptedButtons: Qt.NoButton } }
                Row { spacing: 3; height: parent.height; Repeater { model: 7; Rectangle { width: 2; height: 3+(lisa.recording ? lisa.inputLevel : lisa.playingSpeech ? lisa.audioLevel : 0)*(5+(index%3)*4); color: "#d0b7ee"; radius: 1; anchors.verticalCenter: parent.verticalCenter; Behavior on height { NumberAnimation { duration: 70 } } } } }
                Text { text: root.historyVisible ? "Close chat" : "History"; color: "#ddd0ed"; font.pixelSize: 10; MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.historyVisible=!root.historyVisible } }
                Text { text: "Stop"; color: "#e6d8ee"; font.pixelSize: 10; MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: lisa.stop() } }
                Text { text: "Hide"; color: "#bdaecc"; font.pixelSize: 10; MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: { root.chatVisible=false; root.historyVisible=false } } }
            }
        }
    }
    SoftButton { objectName: "focusButton"; visible: !root.chatVisible; anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin: 24; text: "Show chat"; onClicked: root.chatVisible=true }
    Glass {
        id: history
        objectName: "chatHistory"
        backdrop: scene; animate: root.ambientMotion; cornerRadius: 24; tint: "#c013192b"
        visible: root.historyVisible && root.chatVisible
        anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: dock.top; anchors.bottomMargin: 14
        width: dock.width; height: Math.min(400,root.height-dock.height-150)
        ColumnLayout {
            anchors.fill: parent; anchors.margins: 18; spacing: 12
            RowLayout { Layout.fillWidth: true; Text { text: "OUR CONVERSATION"; font.pixelSize: 10; font.letterSpacing: 1.5; color: "#ded1f0" } Item { Layout.fillWidth: true } SoftButton { text: "Clear"; padding: 5; onClicked: lisa.clearChat() } SoftButton { text: "×"; padding: 5; onClicked: root.historyVisible=false } }
            ListView {
                id: chatList; Layout.fillWidth: true; Layout.fillHeight: true; clip: true; spacing: 12; model: lisa.messages
                ScrollBar.vertical: ScrollBar {}
                onCountChanged: Qt.callLater(function() { chatList.positionViewAtEnd() })
                onVisibleChanged: if (visible) Qt.callLater(function() { chatList.positionViewAtEnd() })
                delegate: Column {
                    required property var modelData
                    width: chatList.width; spacing: 5
                    Text { text: modelData.role==="user" ? "YOU" : modelData.role==="assistant" ? "LISA" : "APP"; font.pixelSize: 9; font.letterSpacing: 1.2; color: "#bd9fde" }
                    Text { width: parent.width; text: modelData.content; textFormat: Text.PlainText; wrapMode: Text.Wrap; color: "#eee7f7"; font.pixelSize: 13; lineHeight: 1.15 }
                }
            }
        }
    }
    Glass {
        id: updateCard; objectName: "updateCard"; backdrop: scene; animate: root.ambientMotion; tint: "#e31a1c30"
        visible: lisa.updateNote!==""; z: 20; x: 22; y: controls.y+controls.height+44; width: Math.min(400,root.width-44); height: updateContents.implicitHeight+32
        ColumnLayout {
            id: updateContents; anchors.fill: parent; anchors.margins: 16; spacing: 12
            RowLayout { Layout.fillWidth: true; Text { text: "LISA UPDATES"; color: "#d8bef6"; font.pixelSize: 10; font.letterSpacing: 1.5 } Item { Layout.fillWidth: true } SoftButton { visible: !lisa.updateInProgress; text: "×"; padding: 4; onClicked: lisa.dismissUpdate() } }
            Text { Layout.fillWidth: true; text: lisa.updateNote; wrapMode: Text.Wrap; color: "#f8f1ff"; font.pixelSize: 13 }
            ProgressBar { Layout.fillWidth: true; visible: lisa.updateInProgress; from: 0; to: 1; value: Math.max(0,lisa.updateProgress); indeterminate: lisa.updateProgress<0 }
            SoftButton { visible: lisa.updateState==="error" && !lisa.updateInProgress; text: "Try again"; onClicked: lisa.checkUpdate() }
        }
    }
    Popup {
        id: wardrobe; anchors.centerIn: Overlay.overlay; width: 420; height: 295; modal: true; padding: 22; closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: Rectangle { radius: 24; color: "#ed191d31"; border.color: "#786490" }
        ColumnLayout { anchors.fill: parent; spacing: 14; Text { text: "Four moods of the day"; color: "#f4eaff"; font.pixelSize: 22 } Text { text: "Same Lisa. Your favourite look."; color: "#b8a9c9"; font.pixelSize: 12 } GridLayout { columns: 2; Layout.fillWidth: true; Repeater { model: ["morning","afternoon","evening","night"]; SoftButton { required property string modelData; Layout.fillWidth: true; text: modelData.charAt(0).toUpperCase()+modelData.slice(1); onClicked: { lisa.setOutfit(modelData); wardrobe.close() } } } } SoftButton { text: "Return to live Lisa"; onClicked: { lisa.liveCharacter(); wardrobe.close() } } }
    }
    Popup {
        id: expressions; anchors.centerIn: Overlay.overlay; width: Math.min(680,root.width-60); height: Math.min(600,root.height-100); modal: true; padding: 22; closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: Rectangle { radius: 24; color: "#ed191d31"; border.color: "#786490" }
        ColumnLayout { anchors.fill: parent; spacing: 14; Text { text: "A face for every feeling"; color: "#f4eaff"; font.pixelSize: 22 } Text { text: "Illustrated poses · saved motion clips"; color: "#b8a9c9"; font.pixelSize: 12 } ScrollView { Layout.fillWidth: true; Layout.fillHeight: true; clip: true; GridLayout { width: parent.width; columns: 4; columnSpacing: 8; rowSpacing: 8; Repeater { model: lisa.moods; SoftButton { required property var modelData; Layout.fillWidth: true; text: modelData.label; onClicked: { lisa.setMood(modelData.id); expressions.close() } } } } } SoftButton { text: "Return to live Lisa"; onClicked: { lisa.liveCharacter(); expressions.close() } } }
    }
    Popup {
        id: framing; anchors.centerIn: Overlay.overlay; width: 380; height: 230; modal: true; padding: 22; closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside
        background: Rectangle { radius: 24; color: "#ed191d31"; border.color: "#786490" }
        ColumnLayout { anchors.fill: parent; Text { text: "Make yourself comfortable"; color: "#f4eaff"; font.pixelSize: 19 } Text { text: "Drag Lisa to move her. Scroll to zoom."; color: "#b8a9c9"; font.pixelSize: 12 } Slider { Layout.fillWidth: true; from: .65; to: 1.8; value: root.zoom; onMoved: root.zoom=value; onPressedChanged: if (!pressed) lisa.saveLayout(root.zoom,390) } SoftButton { text: "Reset framing"; onClicked: root.resetLayout() } }
    }
    Menu {
        id: appMenu
        MenuItem { text: "Wardrobe"; onTriggered: wardrobe.open() }
        MenuItem { text: "Expressions"; onTriggered: expressions.open() }
        MenuItem { text: "Character framing"; onTriggered: framing.open() }
        MenuItem { text: "Choose background…"; onTriggered: lisa.chooseBackground() }
        MenuItem { text: "Reset background"; onTriggered: lisa.resetBackground() }
        MenuSeparator {}
        MenuItem { text: "Memory"; onTriggered: lisa.memory() }
        MenuItem { text: "Motion Studio"; onTriggered: lisa.studio() }
        MenuItem { text: "Test voice"; onTriggered: lisa.testVoice() }
        MenuItem { objectName: "updateButton"; text: lisa.updateInProgress ? "Updating…" : "Check for update"; enabled: !lisa.updateInProgress; onTriggered: lisa.checkUpdate() }
        MenuSeparator {}
        MenuItem { objectName: "desktopShortcutOption"; text: "Add desktop shortcut"; onTriggered: lisa.createDesktopShortcut() }
        MenuItem { text: "Show / hide chat · Ctrl+H"; onTriggered: root.chatVisible=!root.chatVisible }
    }
}
