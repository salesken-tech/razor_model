import json
import time

import requests
from flask import Flask, request, Response, render_template
from src.services import signal_service, scoring_service, text_service, question_extractore
from src.utilities import sken_logger, sken_singleton, db, constants, sken_exceptions
from src.utilities.objects import VadChunk
import jsonpickle

logger = sken_logger.get_logger("main")
sken_singleton.Singletons.get_instance()
db.DBUtils.get_instance()
app = Flask(__name__)


@app.route('/signal_page')
def signal_page():
    """
    This is the UI url for creating signals
    """
    return render_template("signal_creator.html")


@app.route('/match_page')
def match_page():
    """
    URL for UI  for matching the sentence or org_snippets
    """
    try:
        print(signal_service.make_cached_signals_product(constants.fetch_constant("default_task_id")))
        prod_id = signal_service.make_cached_signals_product(constants.fetch_constant("default_task_id"))
        return render_template("match.html")
    except (sken_exceptions.NoSignalFound, sken_exceptions.NoProductFound)as exe:
        resp = Response(exe.message, status=500, mimetype='application/text')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp


@app.route('/sentence_processor', methods=['POST', 'GET'])
def sentence_processor():
    """
    This method gets the tokens from the sentence and returns the synonym of each token
    """
    try:
        signal = request.args.get("signal")
        resp = Response(jsonpickle.encode(text_service.get_synonyms(signal)), status=200, mimetype='application/text')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    except requests.exceptions.ConnectionError as exe:
        logger.error(exe)
        resp = Response("Connection Error", status=500, mimetype='application/text')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp


@app.route('/signal_creator', methods=['POST', 'GET'])
def signal_creator():
    content = request.args.get("json_data")
    content = json.loads(content)
    tokens = content['dict']
    scores = content['scores']
    threshold = content['threshold']
    value = content['value']
    prod_id = content["prod_id"]
    try:
        signal_service.make_product_signal(tokens, scores, threshold, value, prod_id)
        resp = Response("done", status=200, mimetype='application/text')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    except Exception as exe:
        resp = Response("not_done", status=500, mimetype='application/text')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp


@app.route('/delete_signal', methods=['POST', 'GET'])
def delete_product_signal():
    signal_id = request.args.get("signal_id")
    if signal_service.delete_product_signal(signal_id):
        resp = Response("{} signal deleted".format(signal_id), status=200,
                        mimetype='application/text')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    else:
        resp = Response("Couldn't delete {} signal".format(signal_id), status=500,
                        mimetype='application/text')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp


@app.route("/sentence_match", methods=["POST", "GET"])
def sentence_matching():
    sentence = request.form.get("sentence")
    vad_chunk = VadChunk(1, time.time(), time.time() + 1, "Agent", sentence, None, None,
                         None)
    result = scoring_service.vad_chunk_match(vad_chunk, constants.fetch_constant("default_prod_id"))
    output = []
    for item in result:
        output.append({"input_sentence": item.snippet_text, "signal": item.signal_text, "tokens": item.matched_tokens,
                       "score": str(item.score), "threshold": item.threshold, "id": item.signal_id,
                       "html_": ""})

    resp = Response(jsonpickle.encode(output),
                    mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route("/lead_qualification_razor", methods=["POST", "GET"])
def lq_detection_task():
    task_id = request.args.get("task_id")
    try:
        prod_id = signal_service.make_cached_signals_product(task_id)
        result = scoring_service.lq_detection_task(prod_id, task_id)
        resp = Response(jsonpickle.encode(result),
                        mimetype='application/json')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    except (sken_exceptions.NoProductFound, sken_exceptions.NoSignalFound) as exe:
        resp = Response(exe.message, status=500,
                        mimetype='application/text')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    except Exception as e:
        resp = Response(e, status=500,
                        mimetype='application/text')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp


@app.route('/org_match', methods=['POST', 'GET'])
def org_match():
    org_id = request.form.get("org_id")
    result = scoring_service.org_snippet_matching_v2(org_id)
    resp = Response(jsonpickle.encode(result),
                    mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/question_detector', methods=["POST", "GET"])
def question_detector():
    sentence = request.args.get("sentence")
    resp = Response(jsonpickle.encode(question_extractore.get_extracted_questions(sentence)),
                    mimetype='application/json')
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080', debug=True)
