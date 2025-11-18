import flet as ft
import requests
import os
import mimetypes

BACKEND_URL = "https://picshare-hnse.onrender.com"  # 👈 your backend URL


def main(page: ft.Page):
    page.title = "Photogram"
    page.bgcolor = ft.Colors.WHITE
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    

    # --- HEADER ---
    header = ft.Container(
        content=ft.Text("PixShare", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
        alignment=ft.alignment.center,
        padding=10,
        bgcolor=ft.Colors.WHITE,
        border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300)),
        width=page.width,
    )

    # --- FEED PAGE ---
    feed = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)

    def load_feed():
        try:
            resp = requests.get(f"{BACKEND_URL}/feed")
            if resp.ok:
                data = resp.json().get("posts", [])
                feed.controls.clear()
                for post in data:
                    feed.controls.append(
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Image(
                                        src=post["url"],
                                        width=350,
                                        height=300,
                                        fit=ft.ImageFit.COVER,
                                    ),
                                    ft.Text(post["caption"], size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                                    ft.Text(post["created_at"], size=12, color=ft.Colors.GREY),
                                    ft.Divider(),
                                ]
                            ),
                            padding=10,
                        )
                    )
                feed.update()
            else:
                print("Feed load error:", resp.status_code)
        except Exception as e:
            print("Feed load error:", e)

    # --- UPLOAD PAGE ---
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    picked_file = ft.Text("")
    caption_input = ft.TextField(label="Caption", width=300,color=ft.Colors.BLACK)
    message = ft.Text("Please Send The Photo On 8075606623 We Will Upload it later ",weight="bold",color=ft.Colors.RED_300)

    def pick_file(e):
        # Ensure on_result is set
        file_picker.on_result = on_file_picked
        file_picker.pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png", "gif", "webp"])

    selected_file = None

    def on_file_picked(e: ft.FilePickerResultEvent):
        nonlocal selected_file

        if not e.files:
            selected_file = None
            picked_file.value = ""
            page.update()
            return

        selected_file = e.files[0]

        try:
            # FLET 0.25: file bytes are in selected_file.bytes
            if selected_file.bytes:
                selected_file._bytes = selected_file.bytes

            # Desktop fallback (optional)
            elif selected_file.path:
                with open(selected_file.path, "rb") as f:
                    selected_file._bytes = f.read()

            else:
                raise Exception("No file bytes found")

            picked_file.value = selected_file.name

        except Exception as ex:
            print("FILE READ ERROR:", ex)
            selected_file = None
            picked_file.value = "Error reading file"
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ Cannot read file."))
            page.snack_bar.open = True

        page.update()




    def upload_image(e):
        nonlocal selected_file

        if not selected_file:
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ Please pick an image first"))
            page.snack_bar.open = True
            page.update()
            return

        # Check if the file bytes were actually read (i.e., _bytes attribute exists)
        if not hasattr(selected_file, '_bytes') or not selected_file._bytes:
             page.snack_bar = ft.SnackBar(ft.Text("⚠️ File data is missing. The file could not be read from your device."))
             page.snack_bar.open = True
             page.update()
             return

        caption = caption_input.value or ""

        try:
            # 2. Guess the mime type from the file name
            mime_type, _ = mimetypes.guess_type(selected_file.name)
            if mime_type is None:
                # Provide a sensible default if guessing fails
                mime_type = "application/octet-stream"
            
            # Use the dynamically guessed mime_type and the read bytes
            files = {"file": (selected_file.name, selected_file._bytes, mime_type)}

            data = {"caption": caption}

            resp = requests.post(f"{BACKEND_URL}/upload", files=files, data=data)
            print("Upload response:", resp.status_code, resp.text)

            if resp.ok:
                page.snack_bar = ft.SnackBar(ft.Text("✅ Upload successful!"))
                page.snack_bar.open = True
                caption_input.value = ""
                picked_file.value = ""
                selected_file = None # Clear the selected file
                load_feed()
                show_home(None)
            else:
                page.snack_bar = ft.SnackBar(ft.Text(f"❌ Upload failed: {resp.status_code} {resp.text}"))
                page.snack_bar.open = True

        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"⚠️ Network Error: {ex}"))
            page.snack_bar.open = True

        page.update()


    upload_page = ft.Column(
        [
            ft.Text("Upload Photo", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
            ft.ElevatedButton("📁 Pick Image", on_click=pick_file),
            picked_file,
            caption_input,
            message,
            ft.ElevatedButton("⬆️ Upload", on_click=upload_image),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=15,
        expand=True,
    )

    # --- VIEW SWITCHING ---
    main_view = ft.Column([header, feed], expand=True, spacing=0)
    upload_view = ft.Column([header, upload_page], expand=True, spacing=0)

    content_container = ft.Container(content=main_view, expand=True)

    def show_home(e):
        content_container.content = main_view
        page.update()
        load_feed()

    def show_upload(e):
        content_container.content = upload_view
        message
        page.update()

    # --- FIXED BOTTOM NAVIGATION ---
    nav_bar = ft.Container(
        content=ft.Row(
            [
                ft.IconButton(icon=ft.Icons.HOME, icon_color=ft.Colors.BLACK, on_click=show_home),
                ft.IconButton(icon=ft.Icons.ADD_BOX, icon_color=ft.Colors.BLACK, on_click=show_upload),
            ],
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
        ),
        bgcolor=ft.Colors.WHITE,
        border=ft.border.only(top=ft.BorderSide(1, ft.Colors.GREY_300)),
        height=60,
    )

    # --- FINAL PAGE STRUCTURE ---
    page.add(
        ft.Column(
            [
                content_container,
                nav_bar,
            ],
            spacing=0,
            expand=True,
        )
    )
    
    # Set the file picker result handler
    file_picker.on_result = on_file_picked
    load_feed()


ft.app(target=main)