# Generate logic
if generate_btn:
    if not genre or not topic:
        st.markdown('<div class="error-box">⚠️ <strong>Missing Input:</strong> Please fill in both <em>Genre/Artist</em> and <em>Creative Prompt</em> fields</div>', unsafe_allow_html=True)
    else:
        # Show search progress
        if len(genre.split()) > 1 and any(c.isupper() for c in genre):
            with st.status("🔍 Researching artist style on the web...", expanded=True) as status:
                st.write("Searching for production details...")
                time.sleep(0.5)
                st.write("Analyzing vocal techniques...")
                time.sleep(0.5)
                st.write("Generating detailed prompt...")
                
                config = {
                    "genre": genre,
                    "topic": topic,
                    "language": language,
                    "vocalType": vocal_type,
                    "bpm": bpm,
                    "duration": duration
                }
                
                result = generate_suno_prompt(config, max_mode, vocal_directing)
                st.session_state.result = result
                st.session_state.last_config = config
                
                if result.get("success"):
                    status.update(label="✅ Research & Generation Complete!", state="complete")
                else:
                    status.update(label="❌ Generation Failed", state="error")
        else:
            with st.spinner("🤖 Generating with Groq..."):
                config = {
                    "genre": genre,
                    "topic": topic,
                    "language": language,
                    "vocalType": vocal_type,
                    "bpm": bpm,
                    "duration": duration
                }
                result = generate_suno_prompt(config, max_mode, vocal_directing)
                st.session_state.result = result
                st.session_state.last_config = config
        
        st.rerun()
