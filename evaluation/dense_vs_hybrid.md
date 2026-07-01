# Dense-only vs Hybrid Retrieval Comparison

## Query: Is Sindbad Submarine suitable for claustrophobic people?

**Rewritten query:** Is Sindbad Submarine suitable for claustrophobic people?  

**Query class:** out_of_scope  

**Filters:** `{'location': None, 'activity': 'boat_trip', 'page_type': None, 'min_price_eur': None, 'max_price_eur': None}`

### Dense-only top results

1. **Submarine (Sindbad)** — score `0.72810`  
   URL: https://www.egypttravelguide.com/tour/submarine-sindbad  
   Section: Submarine (Sindbad)  
   Snippet: Title: Submarine (Sindbad) Page type: tour Section: Submarine (Sindbad) Price EUR: None Locations: Hurghada, Marsa Alam, Sharm El Sheikh, Sharm el Sheikh, El Gouna, Makadi Bay Activities: snorkeling, diving, culture_hist...
2. **Submarine (Sindbad)** — score `0.71327`  
   URL: https://www.egypttravelguide.com/tour/submarine-sindbad  
   Section: Submarine (Sindbad)  
   Snippet: Title: Submarine (Sindbad) Page type: tour Section: Submarine (Sindbad) Price EUR: None Locations: Hurghada, Marsa Alam, Sharm El Sheikh, Sharm el Sheikh, El Gouna, Makadi Bay Activities: snorkeling, diving, culture_hist...
3. **Semi-Submarine with Snorkeling** — score `0.64327`  
   URL: https://www.egypttravelguide.com/tour/semi-submarine-with-snorkeling  
   Section: Semi-Submarine with Snorkeling  
   Snippet: Title: Semi-Submarine with Snorkeling Page type: tour Section: Semi-Submarine with Snorkeling Price EUR: None Locations: Hurghada, Marsa Alam, Sharm El Sheikh, Sharm el Sheikh, Makadi Bay Activities: snorkeling, boat_tri...

### Hybrid top results

1. **Submarine (Sindbad)** — score `0.01627`  
   URL: https://www.egypttravelguide.com/tour/submarine-sindbad  
   Section: Submarine (Sindbad)  
   Snippet: Title: Submarine (Sindbad) Page type: tour Section: Submarine (Sindbad) Price EUR: None Locations: Hurghada, Marsa Alam, Sharm El Sheikh, Sharm el Sheikh, El Gouna, Makadi Bay Activities: snorkeling, diving, culture_hist...
2. **Submarine (Sindbad)** — score `0.01625`  
   URL: https://www.egypttravelguide.com/tour/submarine-sindbad  
   Section: Submarine (Sindbad)  
   Snippet: Title: Submarine (Sindbad) Page type: tour Section: Submarine (Sindbad) Price EUR: None Locations: Hurghada, Marsa Alam, Sharm El Sheikh, Sharm el Sheikh, El Gouna, Makadi Bay Activities: snorkeling, diving, culture_hist...
3. **Semi-Submarine with Snorkeling** — score `0.01587`  
   URL: https://www.egypttravelguide.com/tour/semi-submarine-with-snorkeling  
   Section: Semi-Submarine with Snorkeling  
   Snippet: Title: Semi-Submarine with Snorkeling Page type: tour Section: Semi-Submarine with Snorkeling Price EUR: None Locations: Hurghada, Marsa Alam, Sharm El Sheikh, Sharm el Sheikh, Makadi Bay Activities: snorkeling, boat_tri...

### Analysis

The retrieval comparison shows that hybrid retrieval performed better overall than dense-only retrieval for this project. Dense-only retrieval was able to find semantically related chunks, but hybrid retrieval was more reliable when the query contained exact terms such as tour names, destination names, activities, or transfer-related keywords.
For example, when the query included a specific tour name or place name, BM25 helped the hybrid retriever match the exact words in the website content. This improved the chance of retrieving chunks that directly answered the user question. Dense retrieval was still useful for broader questions because it captured semantic similarity, but it sometimes returned results that were generally related rather than directly relevant.
Based on the tested queries, hybrid retrieval was selected as the preferred retrieval mode because it combines semantic understanding from FAISS with exact keyword matching from BM25. This makes the system more suitable for travel questions involving destinations, prices, tour types, warnings, and specific locations.


## Query: Compare Sharm El Naga and Orange Bay

**Rewritten query:** Compare Sharm El Naga and Orange Bay  

**Query class:** comparison  

**Filters:** `{'location': None, 'activity': None, 'page_type': None, 'min_price_eur': None, 'max_price_eur': None}`

### Dense-only top results

1. **Orange Bay Island** — score `0.74020`  
   URL: https://www.egypttravelguide.com/tour/orange-bay-island  
   Section: Orange Bay Island  
   Snippet: Title: Orange Bay Island Page type: tour Section: Orange Bay Island Price EUR: None Locations: Hurghada, Marsa Alam, Sharm El Sheikh, Sharm el Sheikh, El Gouna Activities: snorkeling, boat_trip, transfer  Visit the stunn...
2. **Orange Bay Island** — score `0.73671`  
   URL: https://www.egypttravelguide.com/tour/orange-bay-island  
   Section: Orange Bay Island  
   Snippet: Title: Orange Bay Island Page type: tour Section: Orange Bay Island Price EUR: None Locations: Hurghada, Marsa Alam, Sharm El Sheikh, Sharm el Sheikh, El Gouna Activities: snorkeling, boat_trip, transfer  7 hours Easy Es...
3. **Sharm El Naga Snorkeling Trip from Hurghada – Coral Reef & Beach Relaxation** — score `0.72722`  
   URL: https://www.egypttravelguide.com/tour/sharm-el-naga-snorkeling-trip-from-hurghada-coral-reef-beach-relaxation  
   Section: Sharm El Naga Snorkeling Trip from Hurghada – Coral Reef & Beach Relaxation  
   Snippet: Title: Sharm El Naga Snorkeling Trip from Hurghada – Coral Reef & Beach Relaxation Page type: tour Section: Sharm El Naga Snorkeling Trip from Hurghada – Coral Reef & Beach Relaxation Price EUR: None Locations: Hurghada,...

### Hybrid top results

1. **Orange Bay Island** — score `0.01605`  
   URL: https://www.egypttravelguide.com/tour/orange-bay-island  
   Section: Orange Bay Island  
   Snippet: Title: Orange Bay Island Page type: tour Section: Orange Bay Island Price EUR: None Locations: Hurghada, Marsa Alam, Sharm El Sheikh, Sharm el Sheikh, El Gouna Activities: snorkeling, boat_trip, transfer  Visit the stunn...
2. **Sharm El Naga Snorkeling Trip from Hurghada – Coral Reef & Beach Relaxation** — score `0.01587`  
   URL: https://www.egypttravelguide.com/tour/sharm-el-naga-snorkeling-trip-from-hurghada-coral-reef-beach-relaxation  
   Section: Sharm El Naga Snorkeling Trip from Hurghada – Coral Reef & Beach Relaxation  
   Snippet: Title: Sharm El Naga Snorkeling Trip from Hurghada – Coral Reef & Beach Relaxation Page type: tour Section: Sharm El Naga Snorkeling Trip from Hurghada – Coral Reef & Beach Relaxation Price EUR: None Locations: Hurghada,...
3. **Sharm El Naga Snorkeling Trip from Hurghada – Coral Reef & Beach Relaxation** — score `0.01585`  
   URL: https://www.egypttravelguide.com/tour/sharm-el-naga-snorkeling-trip-from-hurghada-coral-reef-beach-relaxation  
   Section: Sharm El Naga Snorkeling Trip from Hurghada – Coral Reef & Beach Relaxation  
   Snippet: Title: Sharm El Naga Snorkeling Trip from Hurghada – Coral Reef & Beach Relaxation Page type: tour Section: Sharm El Naga Snorkeling Trip from Hurghada – Coral Reef & Beach Relaxation Price EUR: None Locations: Hurghada,...

### Analysis

The retrieval comparison shows that hybrid retrieval performed better overall than dense-only retrieval for this project. Dense-only retrieval was able to find semantically related chunks, but hybrid retrieval was more reliable when the query contained exact terms such as tour names, destination names, activities, or transfer-related keywords.
For example, when the query included a specific tour name or place name, BM25 helped the hybrid retriever match the exact words in the website content. This improved the chance of retrieving chunks that directly answered the user question. Dense retrieval was still useful for broader questions because it captured semantic similarity, but it sometimes returned results that were generally related rather than directly relevant.
Based on the tested queries, hybrid retrieval was selected as the preferred retrieval mode because it combines semantic understanding from FAISS with exact keyword matching from BM25. This makes the system more suitable for travel questions involving destinations, prices, tour types, warnings, and specific locations.