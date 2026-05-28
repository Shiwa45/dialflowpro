interface DialpadProps {
  onDial: (digit: string) => void
}

export default function Dialpad({ onDial }: DialpadProps) {
  const buttons = [
    { digit: '1', letters: '' },
    { digit: '2', letters: 'ABC' },
    { digit: '3', letters: 'DEF' },
    { digit: '4', letters: 'GHI' },
    { digit: '5', letters: 'JKL' },
    { digit: '6', letters: 'MNO' },
    { digit: '7', letters: 'PQRS' },
    { digit: '8', letters: 'TUV' },
    { digit: '9', letters: 'WXYZ' },
    { digit: '*', letters: '' },
    { digit: '0', letters: '+' },
    { digit: '#', letters: '' },
  ]

  return (
    <div className="grid grid-cols-3 gap-2">
      {buttons.map((btn) => (
        <button
          key={btn.digit}
          onClick={() => onDial(btn.digit)}
          className="h-16 bg-[#1A1F28] hover:bg-[#242933] rounded-lg flex flex-col items-center justify-center transition-colors"
        >
          <span className="text-2xl font-semibold">{btn.digit}</span>
          {btn.letters && (
            <span className="text-[10px] text-gray-500">{btn.letters}</span>
          )}
        </button>
      ))}
    </div>
  )
}
