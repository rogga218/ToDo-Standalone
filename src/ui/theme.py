from nicegui import ui


def inject_dark_mode_script():
    """
    Injects a script to sync Quasar's 'body--dark' class with Tailwind's 'dark' class on the html root.
    This ensures Tailwind dark mode utilities work correctly when NiceGUI dark mode is toggled.
    """
    ui.add_head_html("""
        <script>
            function syncDark() {
                if (document.body.classList.contains("body--dark")) {
                    document.documentElement.classList.add("dark");
                } else {
                    document.documentElement.classList.remove("dark");
                }
            }

            // Watch for changes on body class
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === "attributes" && mutation.attributeName === "class") {
                        syncDark();
                    }
                });
            });

            // Start observing
            document.addEventListener("DOMContentLoaded", () => {
                const body = document.body;
                if(body) {
                    observer.observe(body, { attributes: true });
                    syncDark(); // Initial sync
                }
            });
        </script>
    """)
