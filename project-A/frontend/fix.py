import re

file_path = r'c:\Users\SHREYASH SHARMA\compiler\project-A\frontend\src\pages\Correlations.tsx'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# For heading 3:
content = content.replace('text-gray-900\">\n            <TrendingUp size={18} className=\"text-brand-500\" /> Correlation vs Co-occurrence Analysis', 'text-gray-100\">\n            <TrendingUp size={18} className=\"text-brand-500\" /> Correlation vs Co-occurrence Analysis')

content = content.replace('text-gray-900\">\n          <BarChart3 size={18} className=\"text-brand-500\" /> Correlation Distribution', 'text-gray-100\">\n          <BarChart3 size={18} className=\"text-brand-500\" /> Correlation Distribution')

# Replace classes in the What does this chart mean section
block_old = '''<p className="text-sm text-gray-700 leading-relaxed mb-2">
              This chart visualizes the relationship between how often two code smells happen to appear in the same file (<span className="font-semibold text-gray-900">Co-occurrences</span>, Y-axis) vs whether they actually have a mathematical statistical relationship (<span className="font-semibold text-gray-900">Correlation</span>, X-axis).
            </p>
            <ul className="text-xs text-gray-600 list-disc pl-5 space-y-1">
              <li><strong className="text-gray-800">Top-Right (Danger Zone):</strong> Smells that happen heavily together AND are statistically linked. Fixing one might fix the other.</li>
              <li><strong className="text-gray-800">Top-Left:</strong> Smells that appear in the same files often by pure coincidence, but don't mathematically drive each other.</li>
              <li><strong className="text-gray-800">Bubble Size:</strong> The overall priority/weight of the interaction. Larger bubbles represent highly toxic pairings.</li>
            </ul>'''

block_new = '''<p className="text-sm text-gray-300 leading-relaxed mb-2">
              This chart visualizes the relationship between how often two code smells happen to appear in the same file (<span className="font-semibold text-gray-100">Co-occurrences</span>, Y-axis) vs whether they actually have a mathematical statistical relationship (<span className="font-semibold text-gray-100">Correlation</span>, X-axis).
            </p>
            <ul className="text-xs text-gray-300 list-disc pl-5 space-y-1">
              <li><strong className="text-gray-100">Top-Right (Danger Zone):</strong> Smells that happen heavily together AND are statistically linked. Fixing one might fix the other.</li>
              <li><strong className="text-gray-100">Top-Left:</strong> Smells that appear in the same files often by pure coincidence, but don't mathematically drive each other.</li>
              <li><strong className="text-gray-100">Bubble Size:</strong> The overall priority/weight of the interaction. Larger bubbles represent highly toxic pairings.</li>
            </ul>'''

content = content.replace(block_old, block_new)

dist_old = '''<p className="text-sm text-gray-600 mb-4 bg-gray-100 border border-gray-300 p-3 rounded-lg leading-relaxed">
          <strong className="text-gray-800 tracking-wide uppercase text-xs block mb-1">What am I looking at?</strong>'''

dist_new = '''<p className="text-sm text-gray-200 mb-4 bg-brand-50 border border-brand-200 p-3 rounded-lg leading-relaxed">
          <strong className="text-gray-100 tracking-wide uppercase text-xs block mb-1">What am I looking at?</strong>'''

content = content.replace(dist_old, dist_new)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
