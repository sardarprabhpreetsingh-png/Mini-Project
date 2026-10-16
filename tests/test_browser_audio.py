import asyncio
import json
import urllib.request
import websockets

async def run_full_suite():
    print("Fetching active Chrome CDP targets...")
    req = urllib.request.urlopen("http://127.0.0.1:9222/json")
    pages = json.loads(req.read().decode())
    target = next(p for p in pages if p.get("type") == "page" and "5173" in p.get("url"))
    ws_url = target["webSocketDebuggerUrl"]
    print("Connected to Chrome page:", ws_url)

    async with websockets.connect(ws_url) as ws:
        msg_id = 1
        async def call(method, params=None):
            nonlocal msg_id
            mid = msg_id
            msg_id += 1
            await ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
            while True:
                r = json.loads(await ws.recv())
                if r.get("id") == mid:
                    return r.get("result", {})

        await call("Page.enable")
        await call("DOM.enable")
        await call("Runtime.enable")

        # 1. Reload the page to start clean
        print("\n--- 1. Reloading http://localhost:5173/ ---")
        await call("Page.reload")
        await asyncio.sleep(2.0)

        # Helper to get file input
        async def get_file_input_id():
            doc = await call("DOM.getDocument")
            res = await call("DOM.querySelector", {"nodeId": doc["root"]["nodeId"], "selector": "input[type=file]"})
            return res.get("nodeId")

        # 2. Upload test_sample.m4a
        print("\n--- 2. Uploading test_sample.m4a ---")
        node_id = await get_file_input_id()
        await call("DOM.setFileInputFiles", {
            "nodeId": node_id,
            "files": ["/Users/sprabhpreetsingh/Mini-Project/tests/test_sample.m4a"]
        })
        await asyncio.sleep(1.0)

        # Inspect player state
        player_info = await call("Runtime.evaluate", {
            "expression": """(() => {
                const audio = document.querySelector('audio');
                const filename = document.querySelector('.audio-filename')?.textContent;
                const filesize = document.querySelector('.audio-filesize')?.textContent;
                const errBox = document.querySelector('.audio-preview-info div[style*="background"]')?.textContent;
                return {
                    found: !!audio,
                    src: audio ? audio.src : null,
                    duration: audio ? audio.duration : null,
                    readyState: audio ? audio.readyState : null,
                    networkState: audio ? audio.networkState : null,
                    filename,
                    filesize,
                    errBox
                };
            })()""",
            "returnByValue": True
        })
        print("Player Info for M4A:", json.dumps(player_info["result"]["value"], indent=2))
        assert player_info["result"]["value"]["found"], "Audio element not found!"
        assert player_info["result"]["value"]["duration"] > 18, f"Duration not loaded properly! Got {player_info['result']['value']['duration']}"
        assert "0:19" in player_info["result"]["value"]["filesize"], f"Filesize duration text missing 0:19! Got {player_info['result']['value']['filesize']}"

        # Test Play / Pause / Seek / Volume on M4A
        print("\n--- Testing Play, Pause, Seeking, Volume on M4A ---")
        # Simulate user gesture click on the page
        await call("Input.dispatchMouseEvent", {"type": "mousePressed", "x": 100, "y": 100, "button": "left", "clickCount": 1})
        await call("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": 100, "y": 100, "button": "left", "clickCount": 1})

        play_test = await call("Runtime.evaluate", {
            "expression": """(async () => {
                const audio = document.querySelector('audio');
                if (!audio) return { error: 'No audio element' };

                let playError = null;
                try {
                    await audio.play();
                } catch (e) {
                    playError = e.message;
                }
                const afterPlayPaused = audio.paused;

                // Let it play 200ms
                await new Promise(r => setTimeout(r, 200));
                const timeAfterPlay = audio.currentTime;

                // Pause
                audio.pause();
                const afterPausePaused = audio.paused;

                // Seek to 5s
                audio.currentTime = 5.0;
                await new Promise(r => setTimeout(r, 100));
                const timeAfterSeek = audio.currentTime;

                // Volume
                audio.volume = 0.6;
                const volumeAfterSet = audio.volume;

                return {
                    playError,
                    afterPlayPaused,
                    timeAfterPlay,
                    afterPausePaused,
                    timeAfterSeek,
                    volumeAfterSet
                };
            })()""",
            "awaitPromise": True,
            "returnByValue": True
        })
        print("Controls test result:", json.dumps(play_test, indent=2))
        val = play_test["result"]["value"]
        assert val["afterPausePaused"] is True, "Audio should be paused!"
        assert abs(val["timeAfterSeek"] - 5.0) < 0.2, f"Seeking to 5.0 failed! Got {val['timeAfterSeek']}"
        assert abs(val["volumeAfterSet"] - 0.6) < 0.05, f"Volume setting failed! Got {val['volumeAfterSet']}"

        # 3. Test Delete / Clear Audio button
        print("\n--- 3. Testing Trash / Delete Button ---")
        trash_res = await call("Runtime.evaluate", {
            "expression": """(() => {
                const trashBtn = document.querySelector('.audio-preview-box button[title="Remove audio"]');
                if (trashBtn) {
                    trashBtn.click();
                    return true;
                }
                return false;
            })()""",
            "returnByValue": True
        })
        await asyncio.sleep(0.5)
        after_trash = await call("Runtime.evaluate", {
            "expression": """(() => {
                const audio = document.querySelector('audio');
                const box = document.querySelector('.audio-preview-box');
                return { hasAudio: !!audio, hasBox: !!box };
            })()""",
            "returnByValue": True
        })
        print("After Trash button click:", json.dumps(after_trash["result"]["value"], indent=2))
        assert not after_trash["result"]["value"]["hasAudio"], "Audio element still exists after clearAudio!"

        # 4. Upload test_sample.wav
        print("\n--- 4. Uploading test_sample.wav ---")
        node_id = await get_file_input_id()
        await call("DOM.setFileInputFiles", {
            "nodeId": node_id,
            "files": ["/Users/sprabhpreetsingh/Mini-Project/tests/test_sample.wav"]
        })
        await asyncio.sleep(1.0)

        wav_info = await call("Runtime.evaluate", {
            "expression": """(() => {
                const audio = document.querySelector('audio');
                const filesize = document.querySelector('.audio-filesize')?.textContent;
                return {
                    found: !!audio,
                    duration: audio ? audio.duration : null,
                    filesize
                };
            })()""",
            "returnByValue": True
        })
        print("WAV info:", json.dumps(wav_info["result"]["value"], indent=2))
        assert wav_info["result"]["value"]["found"], "WAV audio not found!"
        assert wav_info["result"]["value"]["duration"] > 18, "WAV duration not loaded!"

        # 5. Upload backend/samples/crisp_keynote.mp3
        print("\n--- 5. Uploading crisp_keynote.mp3 ---")
        node_id = await get_file_input_id()
        await call("DOM.setFileInputFiles", {
            "nodeId": node_id,
            "files": ["/Users/sprabhpreetsingh/Mini-Project/backend/samples/crisp_keynote.mp3"]
        })
        await asyncio.sleep(1.0)

        mp3_info = await call("Runtime.evaluate", {
            "expression": """(() => {
                const audio = document.querySelector('audio');
                return {
                    found: !!audio,
                    duration: audio ? audio.duration : null,
                    readyState: audio ? audio.readyState : null
                };
            })()""",
            "returnByValue": True
        })
        print("MP3 info:", json.dumps(mp3_info["result"]["value"], indent=2))
        assert mp3_info["result"]["value"]["found"], "MP3 audio not found!"
        assert mp3_info["result"]["value"]["duration"] > 18, "MP3 duration not loaded!"

        # 6. Upload empty.m4a (0 bytes)
        print("\n--- 6. Uploading empty.m4a (0 bytes) ---")
        node_id = await get_file_input_id()
        await call("DOM.setFileInputFiles", {
            "nodeId": node_id,
            "files": ["/Users/sprabhpreetsingh/Mini-Project/tests/empty.m4a"]
        })
        await asyncio.sleep(0.5)

        empty_info = await call("Runtime.evaluate", {
            "expression": """(() => {
                const alertEl = document.querySelector('.glass-card > div[style*="danger-bg"] span');
                return {
                    errorText: alertEl ? alertEl.textContent : null
                };
            })()""",
            "returnByValue": True
        })
        print("Empty file error:", json.dumps(empty_info["result"]["value"], indent=2))
        assert "empty (0 bytes)" in (empty_info["result"]["value"]["errorText"] or ""), "Empty file was not rejected properly!"

        # 7. Test Quick Test Sample button (Pitch Presentation)
        print("\n--- 7. Testing Quick Test Samples (Pitch Presentation) ---")
        sample_click = await call("Runtime.evaluate", {
            "expression": """(() => {
                const pills = Array.from(document.querySelectorAll('.sample-pill'));
                const pitchBtn = pills.find(p => p.textContent.includes('Pitch Presentation'));
                if (pitchBtn) {
                    pitchBtn.click();
                    return true;
                }
                return false;
            })()""",
            "returnByValue": True
        })
        print("Clicked sample button:", sample_click["result"]["value"])
        await asyncio.sleep(1.5)

        sample_player = await call("Runtime.evaluate", {
            "expression": """(() => {
                const audio = document.querySelector('audio');
                const filename = document.querySelector('.audio-filename')?.textContent;
                const filesize = document.querySelector('.audio-filesize')?.textContent;
                return {
                    found: !!audio,
                    filename,
                    filesize,
                    duration: audio ? audio.duration : null,
                    readyState: audio ? audio.readyState : null
                };
            })()""",
            "returnByValue": True
        })
        print("Sample clip player info:", json.dumps(sample_player["result"]["value"], indent=2))
        assert sample_player["result"]["value"]["found"], "Sample audio element not found!"
        assert "pitch_presentation" in sample_player["result"]["value"]["filename"], "Incorrect filename for sample!"
        assert sample_player["result"]["value"]["duration"] > 20, "Sample duration not loaded!"

        print("\n=== ALL TESTS PASSED SUCCESSFULLY! ===")

asyncio.run(run_full_suite())
