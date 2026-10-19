"""Conservative rule-based guards run before retrieval or paid generation."""
import re
EMERGENCY = re.compile(r'\b(chest (?:pain|pressure|tightness)|(?:trouble|difficulty) breathing|shortness of breath|can[\x27’]?t breathe|cannot breathe|severe bleeding|unconscious|passed out|(?:face|facial) droop|sudden (?:weakness|numbness)|slurred speech)\b', re.I)
REQUEST = re.compile(r'\b(diagnos(?:e|is)|prescrib\w*|dosage|what dose|how (?:much|many) .{0,40}(?:take|tablets|pills)|(?:should|can) i (?:take|stop|start) .{0,35}(?:medicine|medication|drug)|do i have .{0,60}|(?:which|what) (?:medicine|medication|treatment))\b', re.I)
UNSAFE_OUTPUT = re.compile(r'\b(you (?:definitely |probably )?have (?:a |an )?(?:disease|diabetes|cancer|anemia)|(?:take|start|increase|decrease) .{0,30}\d+\s*(?:mg|mcg|tablets?|pills?)|i (?:diagnose|prescribe)|you should (?:take|stop taking))\b', re.I)
HINDI_EMERGENCY = re.compile(r'(?:सीने|छाती)\s*में\s*(?:तेज\s*|बहुत\s*)?(?:दर्द|दबाव|जकड़न)|सा[ँं]?स\s*(?:लेने\s*)?में\s*(?:दिक्कत|तकलीफ|कठिनाई)|सा[ँं]?स\s*(?:नहीं\s*आ\s*रही|नहीं\s*ले\s*पा)|(?:बहुत|तेज|गंभीर)\s*(?:खून|रक्तस्राव)|बेहोश|अचानक\s*(?:कमजोरी|सुन्न)|चेहर[ाे]\s*(?:का\s*एक\s*हिस्सा\s*)?(?:लटक|झुक)|बोलने\s*में\s*(?:अचानक\s*)?(?:दिक्कत|लड़खड़ाहट)')
HINDI_REQUEST = re.compile(r'(?:कौन\s*सी|कौनसी|कौन|क्या)\s*(?:दवा|दवाई|गोली|औषधि|इलाज)|(?:कितनी|कितना|कितने)\s*(?:दवा|दवाई|खुराक|डोज|डोज़|गोली|टैबलेट)|(?:दवा|दवाई|गोली|खुराक|डोज़?).{0,35}(?:लूँ|लूं|लेनी|लेना|शुरू|बंद|बढ़ा|घटा)|(?:निदान|डायग्नोसिस|दवा\s*लिख)|(?:क्या\s*मुझे|क्या\s*मैं).{0,40}(?:बीमारी|मधुमेह|डायबिटीज|कैंसर|एनीमिया)')
HINDI_UNSAFE_OUTPUT = re.compile(r'(?:आपको\s*(?:निश्चित\s*रूप\s*से\s*|शायद\s*)?(?:मधुमेह|डायबिटीज|कैंसर|एनीमिया)\s*है|\d+\s*(?:mg|mcg|मिलीग्राम|गोली|गोलियाँ|टैबलेट).{0,25}(?:लें|लीजिए|शुरू\s*करें|बढ़ाएँ|घटाएँ)|आप\s*दवा\s*(?:लें|बंद\s*करें))',re.I)

def guard_question(question):
    if EMERGENCY.search(question) or HINDI_EMERGENCY.search(question):
        return {'answer':'These symptoms may need urgent attention. Seek urgent medical care now or contact your local emergency services. Do not wait for report analysis.', 'sources':[], 'urgent':True}
    if REQUEST.search(question) or HINDI_REQUEST.search(question):
        return {'answer':'I can help explain the wording and values in your report, but I cannot diagnose, prescribe, or give dosages. Please discuss diagnosis and treatment with a qualified healthcare professional.', 'sources':[], 'urgent':False}
    return None
