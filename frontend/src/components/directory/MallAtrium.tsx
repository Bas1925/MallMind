/** Original, lightweight architectural illustration; not a photograph of a real mall. */
export function MallAtrium() {
  return (
    <svg viewBox="0 0 700 540" fill="none" aria-hidden="true" className="atrium-art">
      <defs>
        <linearGradient id="atrium-wall" x1="90" y1="30" x2="580" y2="500" gradientUnits="userSpaceOnUse">
          <stop stopColor="#e9d9bd" /><stop offset="1" stopColor="#c7b18f" />
        </linearGradient>
        <linearGradient id="atrium-sky" x1="350" y1="0" x2="350" y2="380" gradientUnits="userSpaceOnUse">
          <stop stopColor="#c4d8cc" /><stop offset="1" stopColor="#f6ead4" />
        </linearGradient>
        <linearGradient id="atrium-floor" x1="350" y1="315" x2="350" y2="540" gradientUnits="userSpaceOnUse">
          <stop stopColor="#f4e5cc" /><stop offset="1" stopColor="#dec6a3" />
        </linearGradient>
        <filter id="atrium-shadow"><feDropShadow dx="0" dy="10" stdDeviation="12" floodColor="#4b4b2f" floodOpacity=".14" /></filter>
      </defs>
      <path fill="url(#atrium-sky)" d="M0 0h700v540H0z" />
      <path d="M0 0h700L455 150H245Z" fill="#eef0e0" />
      {[100, 200, 300, 400, 500, 600].map((x) => <path key={x} d={`M${x} 0 350 200`} stroke="#bdc5b3" strokeWidth="4" />)}
      <path d="M80 50h540M155 95h390M213 130h274" stroke="#bdc5b3" strokeWidth="4" />
      <path d="M0 0 220 145v225L0 540Z" fill="url(#atrium-wall)" />
      <path d="m700 0-220 145v225l220 170Z" fill="url(#atrium-wall)" />
      <path d="M220 145h260v225H220z" fill="#eee2cd" />
      <path d="M270 355V224a80 80 0 0 1 160 0v131" fill="#c5cbb1" />
      <path d="M287 355V229a63 63 0 0 1 126 0v126" fill="#eee7d3" />
      <path d="M220 360h260l220 180H0Z" fill="url(#atrium-floor)" />
      <path d="M350 360v180M275 360 145 540M425 360l130 180M127 434h446M42 506h616" stroke="#c5b08e" strokeWidth="1" opacity=".65" />
      <path d="m0 202 220 52M480 254l220-52M0 223l220 49M480 272l220-49" stroke="#f7ebd6" strokeWidth="13" />
      <path d="m0 183 220 58M480 241l220-58" stroke="#7b9276" strokeWidth="3" />
      {[28, 85, 142, 198].map((x, i) => <g key={x} stroke="#7b9276" strokeWidth="3">
        <path d={`M${x} ${190 + i * 15}v29`} /><path d={`M${700-x} ${190 + i * 15}v29`} />
      </g>)}
      <path d="M27 171V96q37-50 74 21v72M130 198v-57q28-35 55 16v54" fill="#7b8c76" />
      <path d="M599 189v-72q37-71 74-21v75M515 211v-54q27-51 55-16v57" fill="#617a69" />
      <path d="M20 436V306q39-64 78-13v83ZM124 355v-57q30-43 59-6v32Z" fill="#617a69" />
      <path d="m602 376 78 60V306q-39-64-78-13ZM517 324l59 31v-57q-30-43-59-6Z" fill="#71806a" />
      <path d="M28 306 91 296M132 303l44-9M609 296l64 10M525 294l43 9" stroke="#d1b681" strokeWidth="4" />
      <path d="M45 294v-25l42 11v22M617 302v-22l42-11v25" fill="#f7efde" />
      <text x="56" y="287" fill="#485b48" fontSize="10" transform="rotate(13 56 287)" fontFamily="Georgia">café</text>
      <text x="622" y="291" fill="#485b48" fontSize="9" transform="rotate(-13 622 291)" fontFamily="Georgia">studio</text>
      <g filter="url(#atrium-shadow)">
        <path d="M303 0v61M397 0v61" stroke="#566c57" strokeWidth="2" />
        <rect x="286" y="58" width="128" height="62" rx="3" fill="#254e3e" />
        <text x="350" y="86" textAnchor="middle" fill="#f4ecd9" fontFamily="Georgia" fontSize="25" letterSpacing="6">NOVA</text>
        <text x="350" y="104" textAnchor="middle" fill="#c4d6c3" fontFamily="sans-serif" fontSize="7" letterSpacing="2.5">A PLACE TO WANDER</text>
      </g>
      <ellipse cx="350" cy="430" rx="73" ry="24" fill="#4f6349" opacity=".12" />
      <path d="m297 400 11 35q42 20 84 0l11-35" fill="#be9270" />
      <ellipse cx="350" cy="400" rx="53" ry="17" fill="#72866b" />
      <path d="M350 400V254m0 82-28-32m28 2 32-40" stroke="#795f43" strokeWidth="6" />
      <g fill="#446e50">
        <ellipse cx="325" cy="280" rx="32" ry="48" transform="rotate(-35 325 280)" />
        <ellipse cx="377" cy="250" rx="32" ry="47" transform="rotate(29 377 250)" />
        <ellipse cx="349" cy="227" rx="32" ry="49" fill="#68845a" />
        <ellipse cx="305" cy="248" rx="23" ry="36" fill="#7d9568" transform="rotate(-33 305 248)" />
        <ellipse cx="388" cy="291" rx="27" ry="35" fill="#577c55" transform="rotate(42 388 291)" />
      </g>
      <g fill="#294d3d"><ellipse cx="208" cy="387" rx="8" ry="2" opacity=".2" /><circle cx="207" cy="351" r="5" /><path d="m202 359-2 19h14l-3-19ZM204 377l-1 10m7-10 3 10" stroke="#294d3d" strokeWidth="3" /></g>
      <g fill="#956645"><circle cx="474" cy="388" r="6" /><path d="m470 397-6 26h21l-5-26ZM471 422l-1 18m10-18 3 18" stroke="#956645" strokeWidth="4" /></g>
      <path d="M0 490q75-56 115 50H0ZM700 490q-75-56-115 50h115Z" fill="#345c44" />
      <path d="m31 540-7-68m20 68 22-49m605 49 7-68m-20 68-22-49" stroke="#87a17b" strokeWidth="4" />
    </svg>
  );
}
