# Song Title Overlay System - Flow Chart

```mermaid
flowchart TD
    A[User Opens SuperCut Application] --> B[User Interface Loads]
    B --> C{Song Title Checkbox Enabled?}
    
    C -->|No| Z[Skip Song Title Processing]
    C -->|Yes| D[User Configures Settings]
    
    D --> D1[Font Selection]
    D --> D2[Color & Background]
    D --> D3[Position X,Y %]
    D --> D4[Scale & Effects]
    D --> D5[Start Time]
    D --> D6[Text Effects]
    
    D1 --> E[User Selects MP3 Files]
    D2 --> E
    D3 --> E
    D4 --> E
    D5 --> E
    D6 --> E
    
    E --> F[User Starts Video Generation]
    F --> G[VideoWorker.run() Called]
    
    G --> H{use_song_title_overlay == True?}
    H -->|No| Z
    H -->|Yes| I[Initialize song_title_pngs List]
    
    I --> J[Loop Through Selected MP3 Files]
    J --> K[Extract MP3 Title from Metadata]
    
    K --> K1[extract_mp3_title function]
    K1 --> K2{ID3 Tags Available?}
    K2 -->|Yes| K3[Use Metadata Title]
    K2 -->|No| K4[Use Filename as Title]
    K3 --> L[Create Temporary PNG Path]
    K4 --> L
    
    L --> M[create_song_title_png function]
    M --> M1[Create 1920x240 Image Canvas]
    M1 --> M2[Apply Background Settings]
    M2 --> M3[Load Font Configuration]
    M3 --> M4[Apply Text Effects]
    M4 --> M5[Render Title Text]
    M5 --> M6[Save PNG File]
    
    M6 --> N[Add to song_title_pngs Array]
    N --> N1[Store: PNG path, title, x%, y%, start_at]
    
    N1 --> O{More MP3 Files?}
    O -->|Yes| J
    O -->|No| P[Calculate Song Durations]
    
    P --> Q[Create Extra Overlays List]
    Q --> R[Loop Through Song Durations]
    
    R --> R1{First Song?}
    R1 -->|Yes| R2[Start at user_start_at time]
    R1 -->|No| R3[Start at song boundary]
    
    R2 --> R4[Calculate overlay duration]
    R3 --> R4
    R4 --> R5[Add to extra_overlays]
    
    R5 --> S{More Songs?}
    S -->|Yes| R
    S -->|No| T[Pass to FFmpeg Utils]
    
    T --> U[build_filter_graph function]
    U --> V[Song Title Overlay Filter Graph]
    
    V --> V1[Scale PNG: scale = song_title_scale_percent/100]
    V1 --> V2[Calculate Position: x=(W-w)*x_percent/100]
    V2 --> V3[Calculate Y Position: y=(H-h)*(1-y_percent/100)]
    V3 --> V4[Apply Animation Effect]
    
    V4 --> V5{song_title_effect Type}
    V5 -->|fadeinout| V6[Apply Fade In + Fade Out]
    V5 -->|fadein| V7[Apply Fade In Only]
    V5 -->|fadeout| V8[Apply Fade Out Only] 
    V5 -->|zoompan| V9[Apply Zoom Pan Effect]
    V5 -->|none| V10[No Animation Effect]
    
    V6 --> W[Create Filter Chain]
    V7 --> W
    V8 --> W
    V9 --> W
    V10 --> W
    
    W --> X[Add to FFmpeg Filter Graph]
    X --> Y[Process Video with Overlays]
    Y --> Y1[FFmpeg Execution]
    Y1 --> Y2[Render Final Video]
    
    Y2 --> Y3[Cleanup Temporary PNG Files]
    Y3 --> AA[Video Generation Complete]
    
    Z --> AA

    style A fill:#e1f5fe
    style AA fill:#c8e6c9
    style C fill:#fff3e0
    style H fill:#fff3e0
    style K2 fill:#fff3e0
    style R1 fill:#fff3e0
    style V5 fill:#fff3e0
    style D fill:#f3e5f5
    style M fill:#f3e5f5
    style V fill:#f3e5f5
```

## Key Components Breakdown

### 1. **UI Configuration Phase**
- User enables song title checkbox in main_ui.py
- Configures font, color, position, effects, and timing
- Settings stored in instance variables

### 2. **Title Extraction Phase** 
- `extract_mp3_title()` in utils.py
- Attempts ID3 metadata extraction
- Falls back to filename if metadata unavailable

### 3. **PNG Generation Phase**
- `create_song_title_png()` in utils.py  
- Creates 1920x240 canvas
- Applies fonts, colors, backgrounds, text effects
- Saves temporary PNG files

### 4. **Timing Calculation Phase**
- Video worker calculates song durations
- First title starts at user-specified time
- Subsequent titles start at song boundaries
- Each title duration matches its song duration

### 5. **FFmpeg Processing Phase**
- `build_filter_graph()` in ffmpeg_utils.py
- Creates filter chains for each overlay
- Applies scaling, positioning, and effects
- Integrates with main video filter graph

### 6. **Rendering & Cleanup Phase**
- FFmpeg processes video with overlays
- Temporary PNG files are cleaned up
- Final video output generated

## Decision Points

| Decision | Condition | Path |
|----------|-----------|------|
| Enable Processing | `song_title_checkbox.isChecked()` | Process or Skip |
| Title Source | ID3 metadata exists | Metadata or Filename |
| Start Timing | First song vs others | User time or Song boundary |
| Animation Type | `song_title_effect` setting | Fade/Zoom/None |

## Data Flow

```
MP3 Files → Title Extraction → PNG Generation → Timing Calculation → FFmpeg Filters → Final Video
```

This flowchart shows the complete journey from user input to final video output, highlighting all the key decision points and processing stages in the song title overlay system.