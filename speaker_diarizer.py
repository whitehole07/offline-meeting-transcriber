#!/usr/bin/env python3
"""
Speaker Diarization Module for Meeting Agent
Easy to integrate with main transcriber
"""

import logging
import warnings
from pathlib import Path
from typing import List, Dict, Optional
import numpy as np
import torch

# Suppress warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

class SpeakerDiarizer:
    """
    Speaker diarization using SpeechBrain embeddings and Whisper segments.
    
    Usage:
        diarizer = SpeakerDiarizer(source_model_path, savedir_model_path)
        segments = diarizer.diarize("audio.wav")
        formatted_text = diarizer.format_output(segments)
    """
    
    def __init__(self, source_model_path, savedir_model_path, gap_tolerance: float = 2.0):
        """
        Initialize the speaker diarizer.
        
        Args:
            gap_tolerance: Maximum gap in seconds between segments to merge them
        """
        self.source_model_path = source_model_path
        self.savedir_model_path = savedir_model_path
        self.gap_tolerance = gap_tolerance
        self.embedding_model = None
        self._load_model()
    
    def _load_model(self):
        """Load SpeechBrain speaker embedding model"""
        try:
            from speechbrain.pretrained import EncoderClassifier
            from speechbrain.utils.fetching import LocalStrategy
            
            self.embedding_model = EncoderClassifier.from_hparams(
                source=self.source_model_path,
                savedir=self.savedir_model_path,
                local_strategy=LocalStrategy.COPY,        # ← avoids symlinks on Windows
                overrides={"pretrained_path": self.source_model_path}, # ensure all paths are local
            )
            logger.info("Speaker embedding model loaded")
            
        except Exception as e:
            logger.error(f"Failed to load speaker model: {e}")
            self.embedding_model = None
    
    
    def _extract_segment(self, audio_file: str, start: float, end: float) -> np.ndarray:
        """Extract audio segment and convert to mono"""
        try:
            import librosa
            audio, sr = librosa.load(audio_file, sr=16000, mono=True, offset=start, duration=end-start)
            return audio
        except Exception as e:
            logger.error(f"Error extracting segment {start}-{end}: {e}")
            return np.array([])
    
    def _get_embedding(self, audio: np.ndarray) -> Optional[np.ndarray]:
        """Get speaker embedding from audio segment"""
        if self.embedding_model is None or len(audio) < 1600:
            return None
        
        try:
            with torch.no_grad():
                embedding = self.embedding_model.encode_batch(torch.tensor(audio).unsqueeze(0))
                return embedding.squeeze().numpy()
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None
    
    def _cluster_speakers(self, embeddings: List[np.ndarray]) -> List[int]:
        """Use clustering to determine optimal number of speakers"""
        if len(embeddings) <= 3:
            return list(range(len(embeddings)))
        
        max_clusters = min(6, len(embeddings))
        best_score = -1
        best_labels = None
        
        for n_clusters in range(2, max_clusters + 1):
            try:
                from sklearn.cluster import AgglomerativeClustering
                from sklearn.metrics import silhouette_score
                
                clustering = AgglomerativeClustering(
                    n_clusters=n_clusters,
                    linkage='average',
                    metric='cosine'
                )
                labels = clustering.fit_predict(embeddings)
                score = silhouette_score(embeddings, labels, metric='cosine')
                
                if score > best_score:
                    best_score = score
                    best_labels = labels
                    
            except Exception as e:
                logger.warning(f"Clustering failed for {n_clusters} clusters: {e}")
                continue
        
        num_speakers = len(set(best_labels)) if best_labels is not None else 2
        logger.info(f"Best clustering: {num_speakers} speakers with score {best_score:.3f}")
        return best_labels.tolist() if best_labels is not None else list(range(len(embeddings)))
    
    def _merge_segments(self, segments: List[Dict]) -> List[Dict]:
        """Merge consecutive segments from the same speaker"""
        if not segments:
            return []
        
        merged = []
        current = segments[0].copy()
        
        for segment in segments[1:]:
            if (current['speaker'] == segment['speaker'] and 
                segment['start'] - current['end'] <= self.gap_tolerance):
                # Merge segments
                current['end'] = segment['end']
                current['text'] += " " + segment['text']
            else:
                # Add current and start new
                merged.append(current)
                current = segment.copy()
        
        merged.append(current)
        return merged
    
    def diarize(self, audio_file: str, transcription_segments: List[Dict]) -> List[Dict]:
        """
        Perform speaker diarization on audio file using provided transcription segments.
        
        Args:
            audio_file: Path to audio file
            transcription_segments: List of transcription segments with start, end, and text
            
        Returns:
            List of segments with speaker, timing, and text information
        """
        if not Path(audio_file).exists():
            logger.error(f"Audio file not found: {audio_file}")
            return []
        
        if not transcription_segments:
            logger.error("No transcription segments provided")
            return []
        
        logger.info(f"Using {len(transcription_segments)} transcription segments for diarization")
        
        # Collect embeddings from transcription segments
        embeddings = []
        segment_info = []
        
        for segment in transcription_segments:
            start, end = segment['start'], segment['end']
            text = segment.get('text', '').strip()
            
            audio_segment = self._extract_segment(audio_file, start, end)
            embedding = self._get_embedding(audio_segment)
            
            if embedding is not None:
                embeddings.append(embedding)
                segment_info.append({'start': start, 'end': end, 'text': text})
        
        if not embeddings:
            logger.error("No valid embeddings generated")
            return []
        
        # Cluster speakers
        speaker_labels = self._cluster_speakers(embeddings)
        
        # Create results
        raw_results = []
        for i, (segment, label) in enumerate(zip(segment_info, speaker_labels)):
            raw_results.append({
                'start': segment['start'],
                'end': segment['end'],
                'speaker': f'SPEAKER_{label:02d}',
                'text': segment['text']
            })
        
        # Merge consecutive segments
        return self._merge_segments(raw_results)
    
    def format_output(self, segments: List[Dict], output_file: str = None) -> str:
        """
        Format diarization results as text.
        
        Args:
            segments: List of diarized segments
            output_file: Optional file to save results
            
        Returns:
            Formatted text string
        """
        lines = []
        for segment in segments:
            start_formatted = f"{int(segment['start']//60):02d}:{int(segment['start']%60):02d}"
            end_formatted = f"{int(segment['end']//60):02d}:{int(segment['end']%60):02d}"
            speaker_num = segment['speaker'].split('_')[1]
            
            if 'text' in segment and segment['text']:
                lines.append(f"SPEAKER {speaker_num} ({start_formatted} - {end_formatted}): {segment['text']}")
            else:
                lines.append(f"SPEAKER {speaker_num} ({start_formatted} - {end_formatted})")
        
        output_text = "\n".join(lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output_text + "\n")
            logger.info(f"Saved to: {output_file}")
        
        return output_text
