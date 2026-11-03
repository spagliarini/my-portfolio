# my-portfolio

A Streamlit portfolio with separate Home, Work Experience, and Education views. Contact information is available in the left sidebar.

The shared profile is stored in [`parsed_cv.json`](./parsed_cv.json) and loaded as-is for every visitor. Visitors cannot update or regenerate it.

To enable the owner-only **Refresh profile from CV** control, configure `PROFILE_REFRESH_PASSWORD` and `GEMINI_API_KEY` in Streamlit secrets (or as environment variables). The control is hidden unless the owner password is configured. After entering the password, regenerate the profile and download the resulting `parsed_cv.json`. Replace the repository copy with that file and deploy the change to make the refreshed profile persistent. A refresh updates the running app instance, but deployment filesystems may not persist changes across restarts.
