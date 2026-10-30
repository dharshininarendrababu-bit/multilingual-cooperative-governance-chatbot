from base64 import b64encode

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session,
    Response,
)

from database import (
    get_all_knowledge,
    add_knowledge,
    get_knowledge,
    update_knowledge,
    delete_knowledge,
    search_knowledge,
    get_all_enquiries,
    add_enquiry,
    get_enquiry,
    answer_enquiry,
    delete_enquiry,
    search_enquiries,
)

from sarvam_voice import (
    transcribe_audio_bytes,
    synthesize_speech,
    is_tts_supported,
    SARVAM_LANG_MAP,
)

app = Flask(__name__)
app.secret_key = "cooperative_chatbot_secret_key_2026"

LANGUAGES = [
    "English",
    "Tamil",
    "Hindi",
    "Telugu",
    "Malayalam",
    "Kannada",
    "Bengali",
    "Marathi",
    "Gujarati",
    "Punjabi",
    "Odia",
    "Assamese",
    "Urdu",
    "Nepali",
    "Konkani",
]


@app.context_processor
def inject_template_data():
    return {"languages": LANGUAGES}


@app.route("/")
def index():
    return render_template("index.html", languages=LANGUAGES)


def normalize_text(text):
    if text is None:
        return ""
    text = str(text).lower().strip()
    for symbol in [
        "?", "!", ".", ",", ";", ":", "-", "_", "(", ")",
        "[", "]", "{", "}", "'", '"', "/", "\\",
    ]:
        text = text.replace(symbol, " ")
    return " ".join(text.split())


def get_words(text):
    normalized = normalize_text(text)
    return normalized.split() if normalized else []


IMPORTANT_KEYWORDS = [
    "pacs", "cooperative", "society", "audit", "membership", "member",
    "bylaw", "rules", "credit", "loan", "agriculture", "government",
    "கூட்டுறவு", "சங்கம்", "உறுப்பினர்", "தணிக்கை", "விதிமுறை", "கடன்", "விவசாயம்",
    "सहकारी", "समिति", "सदस्य", "ऑडिट", "नियम", "ऋण", "कृषि",
]


def calculate_score(user_question, stored_question, stored_language, selected_language):
    user_text = normalize_text(user_question)
    stored_text = normalize_text(stored_question)
    if not user_text or not stored_text:
        return 0

    score = 0
    if user_text == stored_text:
        score += 100

    user_words = set(get_words(user_text))
    stored_words = set(get_words(stored_text))
    score += len(user_words.intersection(stored_words)) * 10

    for keyword in IMPORTANT_KEYWORDS:
        if keyword in user_text and keyword in stored_text:
            score += 20

    if str(stored_language).strip().lower() == str(selected_language).strip().lower():
        score += 25

    return score


def search_answer(user_question, language="English"):
    if not user_question or not user_question.strip():
        return "Please enter your question."

    selected_language = str(language).strip().lower()
    knowledge = get_all_knowledge()

    # Only search records in the selected language.
    language_records = [
        item for item in knowledge
        if str(item.get("language", "")).strip().lower() == selected_language
    ]

    if not language_records:
        return (
            f"Sorry, no knowledge is available in {language} yet.\n\n"
            "Please try another available language or submit an enquiry."
        )

    best_answer = None
    best_score = 0

    for item in language_records:
        score = calculate_score(
            user_question,
            item.get("question", ""),
            item.get("language", ""),
            language,
        )
        if score > best_score:
            best_score = score
            best_answer = item.get("answer", "")

    if best_answer and best_score >= 40:
        return best_answer

    return (
        f"Sorry, I could not find a suitable answer in {language}.\n\n"
        "Please try another cooperative-related question or submit an enquiry to the administrator."
    )


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        question = str(data.get("question", "")).strip()
        language = str(data.get("language", "English")).strip()

        if language not in LANGUAGES:
            language = "English"

        if not question:
            return jsonify({"success": False, "answer": "Please enter your question."}), 400

        answer = search_answer(question, language)
        return jsonify({"success": True, "answer": answer, "language": language})

    except Exception as error:
        print("CHAT ERROR:", error)
        return jsonify({
            "success": False,
            "answer": "An error occurred while processing your question.",
        }), 500


@app.route("/api/voice/transcribe", methods=["POST"])
def voice_transcribe():
    try:
        language = str(request.form.get("language", "English")).strip()
        if language not in LANGUAGES:
            language = "English"

        audio = request.files.get("audio")
        if audio is None:
            return jsonify({"success": False, "message": "No audio file received."}), 400

        audio_bytes = audio.read()
        if not audio_bytes:
            return jsonify({"success": False, "message": "Audio file is empty."}), 400

        result = transcribe_audio_bytes(
            audio_bytes=audio_bytes,
            filename=audio.filename or "voice.webm",
            language_name=language,
            mime_type=audio.mimetype or "audio/webm",
        )

        return jsonify({
            "success": True,
            "transcript": result.get("transcript", ""),
            "detected_language": result.get("language_code"),
        })

    except Exception as error:
        print("STT ERROR:", error)
        return jsonify({
            "success": False,
            "message": str(error),
        }), 500


@app.route("/api/voice/speak", methods=["POST"])
def voice_speak():
    try:
        data = request.get_json(silent=True) or {}
        text = str(data.get("text", "")).strip()
        language = str(data.get("language", "English")).strip()

        if language not in LANGUAGES:
            language = "English"

        if not text:
            return jsonify({"success": False, "message": "No text received."}), 400

        # For Assamese, Urdu, Nepali and Konkani, the frontend uses browser TTS.
        if not is_tts_supported(language):
            return jsonify({
                "success": True,
                "supported": False,
                "message": "Sarvam TTS is not available for this language; browser TTS will be used.",
            })

        audio_bytes = synthesize_speech(text, language)
        if not audio_bytes:
            return jsonify({"success": True, "supported": False})

        return jsonify({
            "success": True,
            "supported": True,
            "audio_base64": b64encode(audio_bytes).decode("ascii"),
            "mime_type": "audio/wav",
        })

    except Exception as error:
        print("TTS ERROR:", error)
        return jsonify({
            "success": False,
            "message": str(error),
        }), 500


@app.route("/enquiry", methods=["POST"])
def submit_enquiry():
    try:
        data = request.get_json(silent=True) or {}
        name = str(data.get("name", "Anonymous")).strip() or "Anonymous"
        question = str(data.get("question", "")).strip()
        language = str(data.get("language", "English")).strip()

        if language not in LANGUAGES:
            language = "English"

        if not question:
            return jsonify({"success": False, "message": "Please enter your question."}), 400

        enquiry_id = add_enquiry(name, question, language)
        return jsonify({
            "success": True,
            "message": "Your enquiry has been submitted successfully.",
            "id": enquiry_id,
        })

    except Exception as error:
        print("ENQUIRY ERROR:", error)
        return jsonify({
            "success": False,
            "message": "Unable to submit your enquiry.",
        }), 500


@app.route("/enquiry/<int:enquiry_id>", methods=["GET"])
def enquiry_status(enquiry_id):
    enquiry = get_enquiry(enquiry_id)
    if enquiry is None:
        return jsonify({"success": False, "message": "Enquiry not found."}), 404

    return jsonify({
        "success": True,
        "id": enquiry["id"],
        "name": enquiry["name"],
        "question": enquiry["question"],
        "language": enquiry["language"],
        "status": enquiry["status"],
        "answer": enquiry.get("answer", "") or enquiry.get("reply", ""),
        "date": enquiry.get("date", ""),
    })


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = str(request.form.get("username", "")).strip()
        password = str(request.form.get("password", "")).strip()

        if username == "admin" and password == "admin123":
            session["admin_logged_in"] = True
            session["admin_username"] = username
            return redirect(url_for("admin_dashboard"))

        return render_template("admin_login.html", error="Invalid username or password.")

    return render_template("admin_login.html")


@app.route("/admin")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    enquiries = get_all_enquiries()
    knowledge = get_all_knowledge()

    total_enquiries = len(enquiries)
    pending_enquiries = sum(1 for item in enquiries if str(item.get("status", "Pending")).lower() == "pending")
    answered_enquiries = sum(1 for item in enquiries if str(item.get("status", "")).lower() == "answered")

    return render_template(
        "admin.html",
        admin_username=session.get("admin_username", "Admin"),
        total_enquiries=total_enquiries,
        pending_enquiries=pending_enquiries,
        answered_enquiries=answered_enquiries,
        total_knowledge=len(knowledge),
        enquiries=enquiries,
    )


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


@app.route("/admin/enquiries")
def admin_enquiries():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    keyword = request.args.get("search", "").strip()
    status = request.args.get("status", "").strip()
    enquiries = search_enquiries(keyword=keyword, status=status)

    return render_template(
        "enquiries.html",
        enquiries=enquiries,
        search=keyword,
        selected_status=status,
        admin_username=session.get("admin_username", "Admin"),
    )


@app.route("/admin/enquiry/<int:enquiry_id>/answer", methods=["POST"])
def admin_answer_enquiry(enquiry_id):
    if not session.get("admin_logged_in"):
        return jsonify({"success": False, "message": "Unauthorized."}), 401

    data = request.get_json(silent=True) or {}
    answer = str(data.get("answer", "")).strip()
    if not answer:
        return jsonify({"success": False, "message": "Answer cannot be empty."}), 400

    updated = answer_enquiry(enquiry_id, answer)
    if not updated:
        return jsonify({"success": False, "message": "Enquiry not found."}), 404

    return jsonify({"success": True, "message": "Enquiry answered successfully."})


@app.route("/admin/enquiry/<int:enquiry_id>/delete", methods=["POST"])
def admin_delete_enquiry(enquiry_id):
    if not session.get("admin_logged_in"):
        return jsonify({"success": False, "message": "Unauthorized."}), 401

    deleted = delete_enquiry(enquiry_id)
    if not deleted:
        return jsonify({"success": False, "message": "Enquiry not found."}), 404

    return jsonify({"success": True, "message": "Enquiry deleted successfully."})


@app.route("/admin/knowledge")
def admin_knowledge():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    keyword = request.args.get("search", "").strip()
    language = request.args.get("language", "").strip()
    category = request.args.get("category", "").strip()

    knowledge = search_knowledge(keyword=keyword, language=language, category=category)

    return render_template(
        "knowledge.html",
        knowledge=knowledge,
        search=keyword,
        selected_language=language,
        selected_category=category,
        admin_username=session.get("admin_username", "Admin"),
    )


@app.route("/admin/knowledge/add", methods=["POST"])
def admin_add_knowledge():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    question = str(request.form.get("question", "")).strip()
    answer = str(request.form.get("answer", "")).strip()
    language = str(request.form.get("language", "English")).strip()
    category = str(request.form.get("category", "General")).strip()

    if not question or not answer:
        return redirect(url_for("admin_knowledge"))

    add_knowledge(question, answer, language, category)
    return redirect(url_for("admin_knowledge"))


@app.route("/admin/knowledge/edit/<int:item_id>", methods=["GET", "POST"])
def admin_edit_knowledge(item_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    item = get_knowledge(item_id)
    if item is None:
        return "Knowledge item not found.", 404

    if request.method == "POST":
        question = str(request.form.get("question", "")).strip()
        answer = str(request.form.get("answer", "")).strip()
        language = str(request.form.get("language", "English")).strip()
        category = str(request.form.get("category", "General")).strip()

        if not question or not answer:
            return render_template(
                "edit_knowledge.html",
                item=item,
                error="Question and answer are required.",
            )

        updated = update_knowledge(item_id, question, answer, language, category)
        if not updated:
            return "Unable to update knowledge item.", 500

        return redirect(url_for("admin_knowledge"))

    return render_template("edit_knowledge.html", item=item)


@app.route("/admin/knowledge/delete/<int:item_id>", methods=["POST"])
def admin_delete_knowledge(item_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    delete_knowledge(item_id)
    return redirect(url_for("admin_knowledge"))


@app.errorhandler(404)
def page_not_found(error):
    return "<h1>404 - Page Not Found</h1><a href='/'>Go to Home</a>", 404


@app.errorhandler(500)
def internal_server_error(error):
    return "<h1>500 - Internal Server Error</h1><a href='/'>Go to Home</a>", 500


if __name__ == "__main__":
    print("==============================================")
    print(" MULTILINGUAL COOPERATIVE CHATBOT")
    print("==============================================")
    print("Website : http://127.0.0.1:5000/")
    print("Admin   : http://127.0.0.1:5000/admin/login")
    print("Languages:", ", ".join(LANGUAGES))
    print("==============================================")
    app.run(host="127.0.0.1", port=5000, debug=True)
