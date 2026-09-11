import html
import json

import streamlit.components.v1 as components


def render_react_shell(title, subtitle, role, active="Overview"):
    """Render a dependency-free React presentation shell inside Streamlit.

    The component is intentionally presentational. Streamlit remains responsible
    for authentication, Firebase reads/writes, chatbot execution, and all form
    actions, so no browser-side credentials or duplicate state are introduced.
    """
    payload = json.dumps(
        {
            "title": title,
            "subtitle": subtitle,
            "role": role,
            "active": active,
        }
    ).replace("</", "<\\/")
    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle)
    safe_role = html.escape(role)
    components.html(
        f"""
        <div id="careflow-shell"></div>
        <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
        <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
        <style>
          * {{ box-sizing: border-box; }}
          body {{ margin: 0; background: transparent; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
          .shell {{ display: flex; align-items: center; justify-content: space-between; gap: 18px; padding: 18px 22px; border: 1px solid #dcebe8; border-radius: 16px; background: linear-gradient(110deg, #f1faf8, #ffffff); color: #173333; }}
          .identity {{ display: flex; align-items: center; gap: 12px; min-width: 0; }}
          .mark {{ width: 38px; height: 38px; display: grid; place-items: center; border-radius: 12px; color: white; background: #118b83; font-size: 20px; box-shadow: 0 6px 16px #118b8330; }}
          .copy {{ min-width: 0; }} .title {{ margin: 0; font-size: 18px; font-weight: 800; letter-spacing: -.4px; }} .subtitle {{ margin: 4px 0 0; color: #6d8581; font-size: 12px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
          .meta {{ display: flex; align-items: center; gap: 10px; color: #52716d; font-size: 11px; font-weight: 600; white-space: nowrap; }}
          .role {{ padding: 7px 10px; border-radius: 99px; color: #0d6f69; background: #e2f2ee; }} .live {{ display: flex; align-items: center; gap: 5px; }} .live::before {{ content: ""; width: 6px; height: 6px; border-radius: 50%; background: #42b78f; }}
          @media (max-width: 620px) {{ .shell {{ padding: 14px; }} .meta {{ display: none; }} .title {{ font-size: 16px; }} }}
        </style>
        <script>
          const config = {payload};
          const e = React.createElement;
          function Shell() {{
            return e("section", {{ className: "shell", "aria-label": "Careflow workspace" }},
              e("div", {{ className: "identity" }},
                e("div", {{ className: "mark", "aria-hidden": "true" }}, "♡"),
                e("div", {{ className: "copy" }},
                  e("p", {{ className: "title" }}, config.title),
                  e("p", {{ className: "subtitle" }}, config.subtitle)
                )
              ),
              e("div", {{ className: "meta" }},
                e("span", {{ className: "role" }}, config.role),
                e("span", {{ className: "live" }}, "Secure Streamlit session")
              )
            );
          }}
          ReactDOM.createRoot(document.getElementById("careflow-shell")).render(e(Shell));
        </script>
        """,
        height=92,
        scrolling=False,
    )
