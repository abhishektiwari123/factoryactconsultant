# Chulha Aangan — "100 साल पहले" Series, Episode 1: दीवाली 1926

**Upload target:** 1 to 3 November 2026. Diwali is on 8 November, and searches for it peak in the week before.
**Length:** about 9 to 10 minutes. Long videos over 8 minutes can carry mid-roll ads.
**Format:** a long story video in the style of *The Divine Journey*'s "100 साल पहले Navratri" (630K views in 2 days), with a **Chulha Aangan twist**: the story is told from the **kitchen and courtyard of one family**, not from the festival as a whole. That keeps it on-brand with your Shorts (village + food + family emotion).

---

## 1. Make the video

```bash
cd scripts
pip install edge-tts            # Hindi AI voice (free)
# ffmpeg must be installed: https://ffmpeg.org/download.html

# Free images (Pollinations, no key needed):
python generate_history_video.py ../chulha_aangan/ep01_diwali_1926 --music ../resources/music/sitar.mp3

# Better or faster images (Together.ai, about 121 images, roughly $0.30):
export TOGETHER_API_KEY=...
python generate_history_video.py ../chulha_aangan/ep01_diwali_1926 --images together --music ../resources/music/sitar.mp3
```

Output: `chulha_aangan/ep01_diwali_1926/ep01_diwali_1926.mp4`

- **Bad image?** Delete that file from `work/images/` (or replace it with your own, same file name) and run the command again. Only that section gets re-rendered.
- **Making images yourself** (Leonardo, Ideogram, Meta AI, Gemini): every prompt is in `prompts.txt` with its file name. Save the images into `work/images/` and run with `--images manual`.
- **Your own voice or ElevenLabs:** put `seg_01.mp3` … `seg_25.mp3` in `work/audio/` before running. The script uses your files instead of the AI voice.
- **Test without internet:** add `--placeholder`. It uses coloured frames and silent audio to check the timing.

**Music:** take soft sitar, flute or tabla instrumentals from YouTube Studio → **Audio Library** (search "Indian", "sitar"). They are free and safe for monetization.
**Sound effects** like temple bells, rooster crows and crackling fire make a big difference. Add them in CapCut after rendering if you want to take it further.

### Make it look closer to the reference
The reference uses moving AI **video clips**, not still images. For the best result, animate 10 to 15 key shots (the hook, the diyas, the puja, the aerial village at night) with an image-to-video tool, using the images from `work/images/`:
- **Wan 2.1** (your Colab notebook `Wan2_1_Video_Generator.ipynb`, free)
- Kling / Hailuo / Veo (paid, better quality)

Then swap those clips in using CapCut.

---

## 2. Title (pick one)

1. **100 साल पहले दीवाली कैसी होती थी? | 1926 के गाँव का चूल्हा-आंगन | Hindi Story** ← recommended
2. 1926 की दीवाली: जब बिजली नहीं थी, पर घर रोशन थे | 100 Years Ago India
3. 100 साल पहले दीवाली पर गाँव में क्या-क्या बनता था? | Old India Diwali

## 3. Thumbnail

**Image prompt (16:9):**
> cinematic photorealistic, 1926 rural India, Diwali night, an elderly grandmother in a white saree and a little girl with two braids sitting in a mud courtyard surrounded by hundreds of glowing clay diyas, clay chulha with fire in the background, warm golden light, dramatic contrast, highly detailed

**Text on thumbnail:** `100 साल पहले की दीवाली` (big, yellow/white) + a small `1926` badge in the corner.
Keep it to 2 or 3 words only. Faces + diya glow = clicks.

## 4. Description

```
आज से 100 साल पहले, 1926 के भारत में दीवाली कैसे मनाई जाती थी? 🪔

जब गाँवों में बिजली नहीं थी, मिठाई बाज़ार से नहीं आती थी, और पटाखों का शोर नहीं था — तब दीवाली का दिल होता था घर का चूल्हा और घर का आंगन।

इस वीडियो में चलिए 1926 के एक गाँव के चूल्हा-आंगन में —
🪔 गोबर-मिट्टी से आंगन की लिपाई और गेरू की सजावट
🪔 कुम्हार के चाक पर बनते दीये और लक्ष्मी-गणेश
🪔 धनतेरस की हाट, बैलगाड़ी और चीनी के खिलौने
🪔 चूल्हे पर घी, खोया, गुझिया, अनरसे और मालपुए
🪔 दीवाली पर सूरन (ज़मीकंद) की सब्ज़ी का रिवाज़
🪔 बेटियों का घरौंदा
🪔 लक्ष्मी पूजा और दीयों से जगमगाता गाँव
🪔 दीये की लौ से बना काजल
🪔 सूप बजाकर दरिद्र भगाना — "ईश्वर पैठें, दरिद्र निकसे"
🪔 गोवर्धन पूजा, अन्नकूट और भाई दूज

इस वीडियो में जानिए:
100 साल पहले दीवाली कैसी होती थी?
1926 में गाँव में दीवाली पर क्या-क्या पकवान बनते थे?
पुराने समय में दीये और लक्ष्मी-गणेश कहाँ से आते थे?
घरौंदा क्यों बनाया जाता है?
दीवाली पर सूरन की सब्ज़ी क्यों बनती है?
सूप बजाकर दरिद्र भगाने की परंपरा क्या है?

आपकी दादी-नानी दीवाली की कौन-सी परंपरा आज भी निभाती हैं? कमेंट में ज़रूर बताइए 👇

अगर आपको गाँव की मिट्टी की ख़ुशबू और पुराने भारत की कहानियाँ पसंद हैं, तो चूल्हा आंगन को Subscribe करें 🔔

शुभ दीपावली 🪔🙏

Disclaimer:
यह वीडियो 1920s के उत्तर भारत के ग्रामीण जीवन, लोक परंपराओं और प्रचलित सांस्कृतिक छवियों पर आधारित एक historical recreation है। अलग-अलग राज्यों, समुदायों और गाँवों में दीवाली मनाने के तरीके अलग रहे हैं। वीडियो के दृश्य AI द्वारा बनाए गए cinematic representation हैं, किसी एक गाँव का exact reconstruction नहीं।

#Diwali #Diwali2026 #100YearsAgo #1926India #OldIndia #Deepawali #VillageLife #IndianCulture #HindiStory #ChulhaAangan #GaonKiDiwali #IndianHistory
```

## 5. Tags

```
100 saal pehle ki diwali, 100 साल पहले की दीवाली, 1926 ki diwali, diwali 1926, 100 years ago india, old india diwali, purani diwali, gaon ki diwali, village diwali, diwali history in hindi, diwali kaise manate the, 100 साल पहले का भारत, 1926 india, old india village life, diwali traditions, gharonda, suran ki sabzi diwali, daridra bhagana soop, govardhan puja, annakoot, bhai dooj, laxmi puja, diwali story hindi, indian culture, hindi story, chulha aangan
```

## 6. AI disclosure
In YouTube Studio, set **"Altered or synthetic content" → Yes**. The visuals are AI-generated and look realistic. This is required, it doesn't hurt reach, and it protects the channel.

---

## Next episodes in this series (same format)
| # | Topic | Upload by |
|---|---|---|
| 2 | 100 साल पहले छठ पूजा कैसी होती थी? | ~10 Nov (Chhath is around 14 Nov) |
| 3 | 100 साल पहले गाँव में सर्दियाँ कैसे कटती थीं? (अलाव, गुड़, सरसों का साग) | Late Nov |
| 4 | 100 साल पहले गाँव में शादी कैसी होती थी? | Early Dec (wedding season) |
| 5 | बिना फ्रिज, बिना गैस: 1926 की रसोई का एक दिन | Any time (evergreen) |
| 6 | 100 साल पहले मकर संक्रांति / खिचड़ी | ~10 Jan |

**Tip:** cut 3 or 4 vertical Shorts from every long video (for example the kajal scene, the soop scene, the gharonda scene). End each one with "पूरी कहानी चैनल पर". Your Shorts audience is already large, so this is the fastest way to send them to the long videos.
