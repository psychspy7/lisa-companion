import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
ApplicationWindow {
    id: root
    visible: false
    width: 1280; height: 800
    minimumWidth: 680; minimumHeight: 520
    title: "LISA · Under maintenance"
    color: "#100d16"
    onClosing: maintenance.quit()
    Shortcut { sequence: "F11"; onActivated: root.visibility === Window.FullScreen ? root.showNormal() : root.showFullScreen() }
    Shortcut { sequence: "Escape"; onActivated: if(root.visibility === Window.FullScreen) root.showNormal() }
    Rectangle { anchors.fill: parent; gradient: Gradient { GradientStop { position: 0; color: "#23162c" } GradientStop { position: 1; color: "#0d101b" } } }
    ColumnLayout {
        anchors.centerIn: parent
        width: Math.min(root.width-64, 620)
        spacing: 22
        Image { Layout.alignment: Qt.AlignHCenter; Layout.preferredWidth: 104; Layout.preferredHeight: 104; source: maintenance.logo; sourceSize.width: 320; fillMode: Image.PreserveAspectFit; smooth: true; mipmap: true }
        Text { Layout.alignment: Qt.AlignHCenter; text: "LISA"; color: "#eee5f3"; font.family: "Segoe UI"; font.pixelSize: 27; font.letterSpacing: 8 }
        Rectangle { Layout.alignment: Qt.AlignHCenter; width: 48; height: 2; color: "#b08bd1"; radius: 1 }
        Text { objectName: "maintenanceTitle"; Layout.fillWidth: true; text: "Under maintenance"; horizontalAlignment: Text.AlignHCenter; color: "#faf3ff"; font.family: "Segoe UI"; font.pixelSize: root.width<780?30:40; font.weight: Font.DemiBold }
        Text { Layout.fillWidth: true; text: "Lisa is taking a short break while we prepare her next chapter."; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap; color: "#b8a9c4"; font.family: "Segoe UI"; font.pixelSize: 16; lineHeight: 1.25 }
        Text { Layout.fillWidth: true; text: "A new 3D room, animated Lisa, and more are in development."; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap; color: "#8f839f"; font.family: "Segoe UI"; font.pixelSize: 13 }
        Item { height: 4 }
        RowLayout {
            Layout.alignment: Qt.AlignHCenter; spacing: 12
            Button {
                id: update
                objectName: "updateButton"
                text: maintenance.busy ? "Please wait…" : "Check for update"
                enabled: !maintenance.busy
                padding: 16; font.family: "Segoe UI"; font.pixelSize: 14
                onClicked: maintenance.checkUpdate()
                contentItem: Text { text: update.text; font: update.font; color: "#f8efff"; horizontalAlignment: Text.AlignHCenter }
                background: Rectangle { radius: 11; color: update.hovered?"#71538b":"#533c6a"; border.color:"#9576ad"; opacity: update.enabled?1:.55 }
            }
            Button {
                id: close
                text: "Close"; padding: 16; font.family: "Segoe UI"; font.pixelSize: 14
                onClicked: maintenance.quit()
                contentItem: Text { text: close.text; font: close.font; color: "#c4b5ce"; horizontalAlignment: Text.AlignHCenter }
                background: Rectangle { radius: 11; color: close.hovered?"#30263b":"#211b2c"; border.color:"#43364e" }
            }
        }
        ProgressBar { Layout.alignment: Qt.AlignHCenter; Layout.preferredWidth: 310; visible:maintenance.busy; indeterminate:maintenance.progress<0; value:Math.max(0,maintenance.progress) }
        Text { Layout.fillWidth: true; text: maintenance.note; color: "#a391b6"; horizontalAlignment: Text.AlignHCenter; wrapMode: Text.WordWrap; font.family: "Segoe UI"; font.pixelSize: 12 }
    }
    Text { anchors.bottom:parent.bottom; anchors.bottomMargin:25; anchors.horizontalCenter:parent.horizontalCenter; text: "KITTY CORP  ·  "+maintenance.version; color:"#675b75";font.family:"Segoe UI";font.pixelSize:10;font.letterSpacing:2 }
}
